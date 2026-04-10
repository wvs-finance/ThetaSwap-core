"""RAN growth pipeline — batch JSON-RPC, response correlation, rate limiting, DuckDB writes, CLI."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Final

import duckdb
import httpx

from scripts.ran_utils import ANGSTROM_HOOK, BLOCK_NUMBER_0, CREATE_TABLE_DDL, encode_uint256


# ── B-P1: Batch JSON-RPC construction ───────────────────────────────────────


def build_rpc_batches(
    *,
    slot: int,
    blocks: list[int],
    batch_size: int = 15,
) -> list[list[dict[str, object]]]:
    """Build JSON-RPC 2.0 batch payloads for eth_getStorageAt.

    Each request gets a globally unique ``id`` (sequential from 1).
    Batches are capped at ``batch_size`` requests each.

    Returns a list of batches, where each batch is a list of JSON-RPC request dicts.
    """
    address: Final[str] = ANGSTROM_HOOK
    slot_hex: Final[str] = encode_uint256(slot)

    all_requests: list[dict[str, object]] = []
    for idx, block in enumerate(blocks, start=1):
        block_hex: str = hex(block)
        all_requests.append(
            {
                "jsonrpc": "2.0",
                "id": idx,
                "method": "eth_getStorageAt",
                "params": [address, slot_hex, block_hex],
            }
        )

    batches: list[list[dict[str, object]]] = []
    for i in range(0, len(all_requests), batch_size):
        batches.append(all_requests[i : i + batch_size])

    return batches


# ── B-P2: Response correlation by ID ────────────────────────────────────────


def correlate_batch_response(
    *,
    batch: list[dict[str, object]],
    responses: list[dict[str, object]],
) -> dict[int, str]:
    """Correlate JSON-RPC batch responses to block numbers using the ``id`` field.

    Takes a single batch of requests and its corresponding responses.
    Responses may arrive in any order.  This function builds an id-to-block lookup
    from the original requests, then maps each response's ``id`` to its block number
    and extracts the ``result`` value.

    Returns a dict mapping block_number (int) -> hex result (str).
    """
    # Build id -> block_number lookup from original requests
    id_to_block: dict[object, int] = {}
    for req in batch:
        req_id: object = req["id"]
        params: list[str] = req["params"]  # type: ignore[assignment]
        block_hex: str = str(params[2])
        block_num: int = int(block_hex, 16)
        id_to_block[req_id] = block_num

    # Correlate by id, never by position
    result: dict[int, str] = {}
    for resp in responses:
        resp_id: object = resp["id"]
        block_num = id_to_block[resp_id]
        result[block_num] = str(resp["result"])

    return result


# ── B-P3: Rate limiting ─────────────────────────────────────────────────────

SAFETY_FLOOR_SECONDS: Final[float] = 1.0


def compute_inter_batch_delay(
    *,
    batch_calls: int,
    cu_per_call: int,
    cups_limit: int,
) -> float:
    """Compute the minimum inter-batch delay in seconds.

    ``batch_calls`` is the number of RPC calls in a single batch.
    ``cu_per_call`` is the compute-unit cost of each call.
    ``cups_limit`` is the provider's compute-units-per-second cap.

    The raw delay is ``(batch_calls * cu_per_call) / cups_limit``.
    A mandatory safety floor of 1.0 second is enforced regardless of
    raw computation.

    Pure function — no sleeping, no side effects.
    """
    raw_delay: float = (batch_calls * cu_per_call) / cups_limit
    return max(raw_delay, SAFETY_FLOOR_SECONDS)


# ── B-P4: DuckDB idempotent writes ────────────────────────────────────────────

_UPSERT_SQL: Final[str] = (
    "INSERT INTO accumulator_samples (block_number, pool_id, global_growth, sampled_at, stride) "
    "VALUES (?, ?, ?, ?, ?) "
    "ON CONFLICT (pool_id, block_number) DO NOTHING"
)


def insert_sample(
    *,
    conn: duckdb.DuckDBPyConnection,
    pool_id: str,
    block_number: int,
    global_growth: str,
    stride: int,
) -> None:
    """Insert a single accumulator sample, ignoring duplicate (pool_id, block_number).

    Idempotent — re-inserting the same PK preserves the original value.
    """
    sampled_at: str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(_UPSERT_SQL, [block_number, pool_id, global_growth, sampled_at, stride])


# ── B-P6: Retry on transient RPC errors ───────────────────────────────────────


class RpcBatchError(Exception):
    """Raised when an RPC batch request exhausts all retries."""


def send_rpc_batch(
    *,
    client: httpx.Client,
    batch: list[dict[str, object]],
    max_retries: int = 3,
    base_delay: float = 0.01,
) -> list[dict[str, object]]:
    """POST a JSON-RPC batch with exponential backoff retry on transient errors.

    Retries on HTTP 429, 5xx, and httpx.TimeoutException.
    Returns the parsed JSON response list on success.
    Raises RpcBatchError after exhausting max_retries.
    """
    import json as _json

    payload: bytes = _json.dumps(batch).encode()
    attempts: int = 0
    total_attempts: Final[int] = 1 + max_retries

    while attempts < total_attempts:
        try:
            response: httpx.Response = client.post("/", content=payload)
            if response.status_code == 200:
                return response.json()  # type: ignore[no-any-return]
            if response.status_code == 429 or response.status_code >= 500:
                attempts += 1
                if attempts < total_attempts:
                    time.sleep(base_delay * (2 ** (attempts - 1)))
                    continue
                raise RpcBatchError(
                    f"HTTP {response.status_code} after {total_attempts} attempts"
                )
            # Non-retryable HTTP error
            raise RpcBatchError(f"HTTP {response.status_code} (non-retryable)")
        except httpx.TimeoutException:
            attempts += 1
            if attempts < total_attempts:
                time.sleep(base_delay * (2 ** (attempts - 1)))
                continue
            raise RpcBatchError(
                f"Timeout after {total_attempts} attempts"
            )


# ── B-P7: Block range validation ──────────────────────────────────────────────


class BlockRangeError(Exception):
    """Raised when the requested block range is invalid."""


def _resolve_latest_block(client: httpx.Client) -> int:
    """Call eth_getBlockNumber to resolve the chain head."""
    import json as _json

    payload: bytes = _json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "eth_getBlockNumber", "params": []}
    ).encode()
    resp: httpx.Response = client.post("/", content=payload)
    data: dict[str, object] = resp.json()
    return int(str(data["result"]), 16)


def validate_block_range(
    *,
    from_block: int,
    to_block: int | str,
    client: httpx.Client | None,
) -> tuple[int, int]:
    """Validate and resolve a block range for the pipeline.

    - from_block must be >= BLOCK_NUMBER_0 (22,972,937)
    - to_block can be an int or the string "latest" (resolved via RPC)
    - from_block must be strictly less than to_block

    Returns (from_block, to_block) as ints.
    Raises BlockRangeError on invalid input.
    """
    if from_block < BLOCK_NUMBER_0:
        raise BlockRangeError(
            f"--from-block must be >= {BLOCK_NUMBER_0} (Angstrom deploy block)"
        )

    resolved_to: int
    if isinstance(to_block, str) and to_block == "latest":
        if client is None:
            raise BlockRangeError("Cannot resolve 'latest' without an RPC client")
        resolved_to = _resolve_latest_block(client)
    else:
        resolved_to = int(to_block)

    if from_block >= resolved_to:
        raise BlockRangeError(
            f"--from-block ({from_block}) must be < --to-block ({resolved_to})"
        )

    return from_block, resolved_to


# ── B-P10: Smart Resume — Skip Already-Fetched Blocks ─────────────────────────


def filter_missing_blocks(
    *,
    conn: duckdb.DuckDBPyConnection,
    pool_id: str,
    blocks: list[int],
) -> list[int]:
    """Return only those blocks NOT already stored in DuckDB for the given pool.

    Pure query function — no mutations.  Preserves input ordering.
    """
    if not blocks:
        return []

    rows = conn.execute(
        "SELECT block_number FROM accumulator_samples "
        "WHERE pool_id = ? AND block_number IN (SELECT UNNEST(?))",
        [pool_id, blocks],
    ).fetchall()

    existing: set[int] = {int(r[0]) for r in rows}
    return [b for b in blocks if b not in existing]


# ── CLI entrypoint ─────────────────────────────────────────────────────────────


def _make_http_client(rpc_url: str) -> httpx.Client:
    """Create an httpx.Client for the given RPC URL.

    Extracted as a module-level function so tests can monkeypatch it.
    """
    return httpx.Client(base_url=rpc_url, timeout=30.0)


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint for the RAN growth pipeline.

    Parses arguments, validates block range, fetches storage data in batches,
    and writes to DuckDB with per-batch commits.
    """
    import argparse
    import os
    import sys
    from pathlib import Path

    from scripts.ran_utils import POOL_REGISTRY

    parser = argparse.ArgumentParser(description="RAN accumulator growth pipeline")
    parser.add_argument("--pool", required=True, choices=list(POOL_REGISTRY.keys()))
    parser.add_argument("--from-block", required=True, type=int)
    parser.add_argument("--to-block", required=True, type=str)
    parser.add_argument("--stride", type=int, default=50)
    parser.add_argument("--db", type=str, default="data/ran_accumulator.duckdb")

    args = parser.parse_args(argv)

    # ── Fix 3: Stride validation ──
    if args.stride < 1:
        print("stride must be >= 1", file=sys.stderr)
        sys.exit(1)

    # ── Check API key ──
    api_key: str | None = os.environ.get("ALCHEMY_API_KEY")
    if not api_key:
        print("ALCHEMY_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    rpc_url: str = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
    pool_cfg: object = POOL_REGISTRY[args.pool]

    client: httpx.Client = _make_http_client(rpc_url)

    # ── Resolve block range ──
    to_block_arg: int | str = args.to_block
    if to_block_arg != "latest":
        to_block_arg = int(to_block_arg)

    try:
        from_block, to_block = validate_block_range(
            from_block=args.from_block,
            to_block=to_block_arg,
            client=client,
        )
    except BlockRangeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    # ── Build block list ──
    blocks: list[int] = list(range(from_block, to_block, args.stride))

    # ── Fix 5: Auto-create data/ directory ──
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)

    # ── Open DuckDB ──
    conn: duckdb.DuckDBPyConnection = duckdb.connect(args.db)
    conn.execute(CREATE_TABLE_DDL)

    # ── B-P10: Smart resume — skip already-fetched blocks ──
    blocks = filter_missing_blocks(
        conn=conn,
        pool_id=pool_cfg.pool_id,  # type: ignore[union-attr]
        blocks=blocks,
    )

    if not blocks:
        print("all blocks already fetched — nothing to do", file=sys.stderr)
        conn.close()
        client.close()
        return

    # ── Pipeline loop (Fix 1: catch RpcBatchError, Fix 4: try/finally for cleanup) ──
    cu_per_call: Final[int] = 20
    cups_limit: Final[int] = 500
    total_blocks: Final[int] = len(blocks)
    fetched: int = 0

    batches = build_rpc_batches(
        slot=pool_cfg.pool_rewards_slot,  # type: ignore[union-attr]
        blocks=blocks,
        batch_size=15,
    )

    try:
        for batch in batches:
            # Fetch with retry
            responses = send_rpc_batch(client=client, batch=batch, max_retries=3, base_delay=0.01)

            # Correlate
            block_to_value = correlate_batch_response(batch=batch, responses=responses)

            # Write to DuckDB
            for block_num, hex_value in block_to_value.items():
                # Normalize: ensure padded 0x + 64 hex chars
                normalized: str = encode_uint256(int(hex_value, 16))
                insert_sample(
                    conn=conn,
                    pool_id=pool_cfg.pool_id,  # type: ignore[union-attr]
                    block_number=block_num,
                    global_growth=normalized,
                    stride=args.stride,
                )

            conn.commit()
            fetched += len(batch)

            # ── Progress on stderr ──
            cu_used: int = fetched * cu_per_call
            pct: float = (fetched / total_blocks * 100) if total_blocks > 0 else 100.0
            delay: float = compute_inter_batch_delay(
                batch_calls=len(batch), cu_per_call=cu_per_call, cups_limit=cups_limit,
            )
            print(
                f"fetched {fetched}/{total_blocks} total | "
                f"{cu_used} CU | {pct:.1f}% | delay {delay:.2f}s",
                file=sys.stderr,
            )

            # Rate limit (skip in tests — delay is near-zero with base_delay=0.01)
            time.sleep(delay)
    except RpcBatchError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()
        client.close()


if __name__ == "__main__":
    main()
