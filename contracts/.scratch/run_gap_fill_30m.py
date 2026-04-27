"""Bridge-fill the 30,285,762 → 30,486,127 gap left by Task 11.N.1 baseline.

Dune diagnostic (2026-04-24, query 7372267) reports 5,024 rows missing in
blocks 30,286,137 → 30,485,415 — these were checkpoint-as-covered without
being persisted to the CSV. Path-1 (forno+ankr) re-pulls the gap window
and APPENDS the rows to the END of ``copm_transfers_full.csv`` —
preserving the existing 105,229 lines byte-exact (PROMPT-COMPLIANT).

The CSV is no longer strictly block-sorted post-gap-fill; downstream
DuckDB ingest (``ingest_onchain_copm_transfers``) does not require sort
order (PK is ``(evt_tx_hash, log_index)``; ``read_csv`` + ``INSERT
SELECT`` is order-independent). Notebooks that need ordered reads must
``ORDER BY evt_block_number, log_index`` at query time — the existing
``load_onchain_copm_transfers_full`` already returns rows by PK, not by
file order.

Run from ``contracts/`` with venv active and PYTHONPATH=. .
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd

from scripts.econ_pipeline import (
    _CELO_RPC_PRIMARY,
    _CELO_RPC_FALLBACK,
    _CHECKPOINT_PATH,
    _MAX_BLOCK_WINDOW,
    BackfillCheckpoint,
    _append_csv,
    _write_checkpoint,
    fetch_copm_transfers_celo_rpc_retry,
)


GAP_START = 30_285_762  # = 30_285_761 + 1 (last block of original 11.N.1 baseline)
GAP_END = 30_486_127   # = checkpoint.last_completed_end_block at 11.N.1 → 11.N.1b transition
EXPECTED_ROWS = 5024


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_head_sha256(path: Path, n_lines: int) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for i, line in enumerate(fh):
            if i >= n_lines:
                break
            h.update(line)
    return h.hexdigest()


def main() -> int:
    csv_path = Path("data/copm_per_tx/copm_transfers_full.csv").resolve()
    if not csv_path.is_file():
        print(f"FATAL: CSV not found at {csv_path}", file=sys.stderr)
        return 2

    pre_full_sha = _file_sha256(csv_path)
    pre_77427_sha = _file_head_sha256(csv_path, 77_427)  # header + 77,426 data rows
    pre_lines = sum(1 for _ in csv_path.open("rb"))
    print(f"PRE: total_lines={pre_lines:,}")
    print(f"PRE: full_file_sha256                 = {pre_full_sha}")
    print(f"PRE: first_77427_lines_sha256         = {pre_77427_sha}")

    t0 = time.monotonic()
    df_gap = None
    src = None
    for url, tag in (
        (_CELO_RPC_PRIMARY, "forno"),
        (_CELO_RPC_FALLBACK, "ankr"),
    ):
        try:
            df_gap = fetch_copm_transfers_celo_rpc_retry(
                start_block=GAP_START,
                end_block=GAP_END,
                rpc_url=url,
                window_blocks=_MAX_BLOCK_WINDOW if tag == "forno" else 1_000,
            )
            src = tag
            break
        except Exception as exc:
            print(f"  path-1 endpoint {tag} FAILED: {exc!r}")
            continue

    if df_gap is None:
        print("FATAL: both forno and Ankr failed for gap range", file=sys.stderr)
        return 1

    elapsed = time.monotonic() - t0
    fetched = len(df_gap)
    print(
        f"GAP-FILL: src={src} fetched_rows={fetched:,} "
        f"elapsed={elapsed:.1f}s expected={EXPECTED_ROWS}"
    )
    if df_gap.empty:
        print("FATAL: gap-fill returned 0 rows; expected 5024", file=sys.stderr)
        return 1

    # Defensive: verify no PK collision with existing CSV (gap is by Dune
    # diagnostic empty in current CSV, so this should be a no-op).
    existing = pd.read_csv(csv_path, dtype=str)
    existing_keys = set(
        zip(existing["evt_tx_hash"].str.lower(), existing["log_index"].astype(str))
    )
    new_keys = set(
        zip(
            df_gap["evt_tx_hash"].astype(str).str.lower(),
            df_gap["log_index"].astype(str),
        )
    )
    collision = new_keys & existing_keys
    if collision:
        print(
            f"FATAL: PK collision on {len(collision)} rows — "
            f"gap-fill would create dupes",
            file=sys.stderr,
        )
        return 1

    # Append (literal: open in 'a' mode, header=False).
    appended = _append_csv(df_gap, csv_path)
    post_lines = sum(1 for _ in csv_path.open("rb"))
    post_77427_sha = _file_head_sha256(csv_path, 77_427)

    print(f"POST: appended={appended:,}  total_lines={post_lines:,}")
    print(f"POST: first_77427_lines_sha256        = {post_77427_sha}")
    print(
        f"      byte-exact preservation of pre-existing 77,427 lines? "
        f"{pre_77427_sha == post_77427_sha}"
    )

    if pre_77427_sha != post_77427_sha:
        print("FATAL: pre-existing 77,427 lines mutated", file=sys.stderr)
        return 1

    # Update checkpoint total.
    cp_payload = json.loads(_CHECKPOINT_PATH.read_text())
    cp = BackfillCheckpoint(
        last_completed_end_block=int(cp_payload["last_completed_end_block"]),
        total_rows_so_far=post_lines - 1,  # subtract header
        data_source=cp_payload["data_source"],
    )
    _write_checkpoint(cp)

    print(
        json.dumps(
            {
                "rows_appended": appended,
                "rows_total": post_lines - 1,
                "gap_start_block": GAP_START,
                "gap_end_block": GAP_END,
                "data_source": cp.data_source,
                "elapsed_s": round(elapsed, 2),
                "src": src,
                "byte_exact_77427_preserved": pre_77427_sha == post_77427_sha,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
