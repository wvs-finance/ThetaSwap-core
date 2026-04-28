"""
Pair D Task 1.1 Step 6 — independent re-pull and re-compute verification.

Picks 3 random months from the persisted Y panel, redownloads the source zip
(blowing away cache), re-computes Y_broad + Y_narrow from scratch, and asserts
each match within 1% tolerance against the persisted parquet value.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pandas as pd

# Re-use the same ingest module for the recompute
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from ingest_geih import (  # noqa: E402
    _build_plans, _ingest_month, _load_manifest, OUT_BROAD, OUT_NARROW,
    DOWNLOADS,
)


TOL = 0.01  # 1% tolerance per dispatch Step 6


def main() -> int:
    if not OUT_BROAD.exists() or not OUT_NARROW.exists():
        print(f"ERROR: outputs not found ({OUT_BROAD}, {OUT_NARROW}); ingest first.")
        return 1

    df_broad = pd.read_parquet(OUT_BROAD)
    df_narrow = pd.read_parquet(OUT_NARROW)

    if len(df_broad) != len(df_narrow):
        print(f"WARN: broad ({len(df_broad)}) and narrow ({len(df_narrow)}) row count mismatch")

    print(f"Persisted broad parquet: {len(df_broad)} rows, "
          f"first {df_broad['timestamp_utc'].iloc[0]}, last {df_broad['timestamp_utc'].iloc[-1]}")

    manifest = _load_manifest()
    plans = _build_plans(manifest)
    plan_by_ym = {(p.year, p.month): p for p in plans}

    # Pick 3 random months from the persisted panel
    rnd = random.Random(20260428)
    sample_idx = rnd.sample(range(len(df_broad)), k=3)
    sample = df_broad.iloc[sample_idx]

    failures: list[str] = []
    for _, row in sample.iterrows():
        ts = row["timestamp_utc"]
        yr, mo = ts.year, ts.month
        plan = plan_by_ym.get((yr, mo))
        if plan is None:
            print(f"  {yr}-{mo:02d}: no plan found, skipping")
            continue

        # Re-pull: delete cache and re-download
        if plan.cache_path.exists():
            print(f"  {yr}-{mo:02d}: removing cached {plan.cache_path.name}")
            plan.cache_path.unlink()

        recomputed = _ingest_month(plan)
        Y_broad_persisted = float(row["Y_raw"])
        Y_broad_re = float(recomputed["Y_broad_raw"])

        # Narrow comparison too
        narrow_row = df_narrow[df_narrow["timestamp_utc"] == ts].iloc[0]
        Y_narrow_persisted = float(narrow_row["Y_raw"])
        Y_narrow_re = float(recomputed["Y_narrow_raw"])

        diff_b = abs(Y_broad_re - Y_broad_persisted) / max(abs(Y_broad_persisted), 1e-9)
        diff_n = abs(Y_narrow_re - Y_narrow_persisted) / max(abs(Y_narrow_persisted), 1e-9)

        ok_b = diff_b < TOL
        ok_n = diff_n < TOL
        status = "OK" if (ok_b and ok_n) else "FAIL"
        print(
            f"  {yr}-{mo:02d}: persisted Y_broad={Y_broad_persisted:.6f} re={Y_broad_re:.6f} "
            f"diff={diff_b*100:.4f}%  | persisted Y_narrow={Y_narrow_persisted:.6f} "
            f"re={Y_narrow_re:.6f} diff={diff_n*100:.4f}%  → {status}"
        )
        if not ok_b:
            failures.append(f"{yr}-{mo:02d} broad diff {diff_b*100:.4f}% > {TOL*100:.0f}%")
        if not ok_n:
            failures.append(f"{yr}-{mo:02d} narrow diff {diff_n*100:.4f}% > {TOL*100:.0f}%")

    if failures:
        print(f"\nVERIFICATION FAILED ({len(failures)} mismatches):")
        for f in failures:
            print(f"  - {f}")
        return 2
    print(f"\nVERIFICATION PASSED — 3/3 months within {TOL*100:.0f}% tolerance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
