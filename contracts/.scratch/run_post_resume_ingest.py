"""Post-resume DuckDB ingest + X_d weekly compute (Task 11.N.1b Step 9).

Re-ingests the now-110,253-row ``copm_transfers_full.csv`` into the
canonical ``onchain_copm_transfers`` table (idempotent ``INSERT OR
REPLACE``) and re-computes the supply + distribution-channel X_d weekly
panel into ``onchain_xd_weekly``.

Preserves Rev-4 ``decision_hash`` and pre-existing
``net_primary_issuance_usd`` rows byte-exact (the
``ingest_onchain_xd_weekly`` helper already uses ``INSERT OR REPLACE``
keyed on ``(week_start, proxy_kind)`` per the Rev-5.2.1 composite-PK
migration).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import duckdb

from scripts.econ_pipeline import (
    ingest_onchain_copm_transfers,
    ingest_onchain_xd_weekly,
)


def main() -> int:
    db_path = Path("data/structural_econ.duckdb").resolve()
    csv_path = Path("data/copm_per_tx/copm_transfers_full.csv").resolve()
    if not db_path.is_file():
        print(f"FATAL: canonical DB missing at {db_path}", file=sys.stderr)
        return 2
    if not csv_path.is_file():
        print(f"FATAL: CSV missing at {csv_path}", file=sys.stderr)
        return 2

    t0 = time.monotonic()
    conn = duckdb.connect(str(db_path))
    try:
        # Pre-state row counts.
        pre_transfers = conn.execute(
            "SELECT COUNT(*) FROM onchain_copm_transfers"
        ).fetchone()[0]
        pre_xd = conn.execute(
            "SELECT proxy_kind, COUNT(*) FROM onchain_xd_weekly "
            "GROUP BY proxy_kind ORDER BY proxy_kind"
        ).fetchall()
        print(f"PRE: onchain_copm_transfers rows = {pre_transfers:,}")
        print(f"PRE: onchain_xd_weekly per proxy_kind = {pre_xd}")

        # 1. Ingest the full CSV (additive — INSERT OR REPLACE on PK).
        n_ingested = ingest_onchain_copm_transfers(conn, csv_path)
        print(f"INGEST: rows pulled from CSV = {n_ingested:,}")

        # 2. Re-compute X_d weekly panel (supply + distribution).
        n_xd = ingest_onchain_xd_weekly(conn)
        print(f"X_d compute: rows written to onchain_xd_weekly = {n_xd:,}")

        # Post-state.
        post_transfers = conn.execute(
            "SELECT COUNT(*) FROM onchain_copm_transfers"
        ).fetchone()[0]
        post_xd = conn.execute(
            "SELECT proxy_kind, COUNT(*) FROM onchain_xd_weekly "
            "GROUP BY proxy_kind ORDER BY proxy_kind"
        ).fetchall()
        print(f"POST: onchain_copm_transfers rows = {post_transfers:,}")
        print(f"POST: onchain_xd_weekly per proxy_kind = {post_xd}")

        # Distribution-channel weekly count breakdown.
        dist_count = conn.execute(
            "SELECT COUNT(*) FROM onchain_xd_weekly "
            "WHERE proxy_kind = 'b2b_to_b2c_net_flow_usd'"
        ).fetchone()[0]
        supply_count = conn.execute(
            "SELECT COUNT(*) FROM onchain_xd_weekly "
            "WHERE proxy_kind = 'net_primary_issuance_usd'"
        ).fetchone()[0]
        print(
            json.dumps(
                {
                    "transfers_total": post_transfers,
                    "xd_weekly_distribution": dist_count,
                    "xd_weekly_supply": supply_count,
                    "wall_time_s": round(time.monotonic() - t0, 2),
                },
                indent=2,
            )
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
