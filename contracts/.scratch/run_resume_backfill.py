"""Driver: invoke resume_copm_transfers_backfill() with the canonical CSV target.

Run from `contracts/` with the venv active. Prints a JSON summary on success.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from scripts.econ_pipeline import resume_copm_transfers_backfill


def main() -> int:
    csv_path = Path("data/copm_per_tx/copm_transfers_full.csv").resolve()
    if not csv_path.is_file():
        print(f"FATAL: CSV not found at {csv_path}", file=sys.stderr)
        return 2
    t0 = time.monotonic()
    try:
        result = resume_copm_transfers_backfill(output_csv=csv_path)
    except Exception as exc:
        print(f"RESUME_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    payload = {
        "rows_added": result.rows_added,
        "rows_total": result.rows_total,
        "data_source": result.data_source,
        "start_block": result.start_block,
        "end_block": result.end_block,
        "wall_time_s": round(result.wall_time_s, 2),
        "paths_attempted": list(result.paths_attempted),
        "paths_skipped_count": len(result.paths_skipped),
        "wall_clock_total_s": round(time.monotonic() - t0, 2),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
