"""Task 1.3: Panel alignment + N verification + persist.

Inner-joins Y_broad + Y_narrow + X (COP/USD lag panel) on monthly UTC timestamp
(month-end convention) and persists `panel_combined.parquet` per plan §1.3 Step 3.

Anti-fishing discipline:
- HALT (typed exception PairDSampleStructurallyPathological) if N_post_lag12 < 75.
- No silent threshold tuning, no fabrication.
- Logit transform applied with explicit float64 contract; raw Y carried through.

Usage: run from worktree root with venv activated.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

WORKTREE = Path("/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom")
DATA = WORKTREE / "contracts/.scratch/simple-beta-pair-d/data"

Y_BROAD = DATA / "geih_young_workers_services_share.parquet"
Y_NARROW = DATA / "geih_young_workers_narrow_share.parquet"
X = DATA / "cop_usd_panel.parquet"
OUT = DATA / "panel_combined.parquet"

N_MIN = 75


class PairDSampleStructurallyPathological(Exception):
    """Raised when post-lag-12 sample falls below N_MIN=75 per spec §3."""


@dataclass(frozen=True)
class FileFingerprint:
    path: Path
    sha256: str
    n_rows: int


def fingerprint(p: Path) -> FileFingerprint:
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    n = pq.read_metadata(p).num_rows
    return FileFingerprint(path=p, sha256=h, n_rows=n)


def load_y(path: Path, label: str) -> pd.DataFrame:
    df = pq.read_table(path).to_pandas()
    # Rename Y_raw / Y_logit / n_young_in_sector to label-specific columns.
    return df.rename(
        columns={
            "Y_raw": f"Y_{label}_raw",
            "Y_logit": f"Y_{label}_logit",
            "n_young_in_sector": f"n_young_in_services_{label}",
        }
    )


def main() -> None:
    print("=== Task 1.3: panel alignment ===")

    fp_broad = fingerprint(Y_BROAD)
    fp_narrow = fingerprint(Y_NARROW)
    fp_x = fingerprint(X)

    print(f"Y_broad sha256:  {fp_broad.sha256}  rows={fp_broad.n_rows}")
    print(f"Y_narrow sha256: {fp_narrow.sha256}  rows={fp_narrow.n_rows}")
    print(f"X sha256:        {fp_x.sha256}  rows={fp_x.n_rows}")

    y_broad = load_y(Y_BROAD, "broad")
    y_narrow = load_y(Y_NARROW, "narrow")
    x_panel = pq.read_table(X).to_pandas()

    # --- Schema invariants pre-join --------------------------------------
    # Both Y parquets carry n_young_employed; assert it matches across broad/narrow
    # (same denominator, only numerator differs by sector breadth).
    merge_check = y_broad[["timestamp_utc", "n_young_employed"]].merge(
        y_narrow[["timestamp_utc", "n_young_employed"]],
        on="timestamp_utc",
        suffixes=("_broad", "_narrow"),
    )
    mismatch = (merge_check["n_young_employed_broad"] != merge_check["n_young_employed_narrow"]).sum()
    if mismatch != 0:
        raise RuntimeError(
            f"n_young_employed differs across broad/narrow Y parquets in {mismatch} rows; "
            "denominators must match — investigate Task 1.1 output before joining."
        )
    print(f"n_young_employed cross-check: PASS ({len(merge_check)} rows agree)")

    # --- Timestamp convention check --------------------------------------
    # Both Y panels and X panel use month-END UTC; assert by sampling head/tail.
    for name, df in [("y_broad", y_broad), ("y_narrow", y_narrow), ("x_panel", x_panel)]:
        ts = df["timestamp_utc"]
        # all timestamps should be the last day of their month
        days = ts.dt.day
        last_of_month = (ts + pd.Timedelta(days=1)).dt.month != ts.dt.month
        if not last_of_month.all():
            raise RuntimeError(f"{name}: not all timestamps are month-end UTC — convention mismatch")
    print("Timestamp convention: month-END UTC across all 3 inputs (CONSISTENT)")

    # --- Inner join ------------------------------------------------------
    # Drop the duplicated era / n_young_employed columns from one side after merge
    y_broad_keep = y_broad[
        ["timestamp_utc", "Y_broad_raw", "Y_broad_logit", "n_young_employed", "n_young_in_services_broad"]
    ]
    y_narrow_keep = y_narrow[["timestamp_utc", "Y_narrow_raw", "Y_narrow_logit", "n_young_in_services_narrow"]]
    x_keep = x_panel[["timestamp_utc", "log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"]]

    joined = y_broad_keep.merge(y_narrow_keep, on="timestamp_utc", how="inner").merge(
        x_keep, on="timestamp_utc", how="inner"
    )
    joined = joined.sort_values("timestamp_utc").reset_index(drop=True)

    n_raw = len(joined)
    print(f"\nInner-join row count (raw): {n_raw}")

    # --- Recompute logit defensively (verify upstream values) -----------
    eps = 1e-12  # guards against exact 0/1 (none expected here; Y bounded ~[0.55, 0.75])
    recomputed_broad = np.log(joined["Y_broad_raw"] / (1 - joined["Y_broad_raw"]))
    recomputed_narrow = np.log(joined["Y_narrow_raw"] / (1 - joined["Y_narrow_raw"]))
    max_drift_broad = float((recomputed_broad - joined["Y_broad_logit"]).abs().max())
    max_drift_narrow = float((recomputed_narrow - joined["Y_narrow_logit"]).abs().max())
    print(f"Logit recompute drift broad: {max_drift_broad:.2e}")
    print(f"Logit recompute drift narrow: {max_drift_narrow:.2e}")
    if max_drift_broad > 1e-9 or max_drift_narrow > 1e-9:
        raise RuntimeError(
            f"Logit values from Task 1.1 disagree with recomputed log(Y/(1-Y)) "
            f"by > 1e-9 (broad={max_drift_broad:.2e}, narrow={max_drift_narrow:.2e})"
        )

    # --- N verification (post-lag-12) ------------------------------------
    lag_cols = ["log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"]
    post_lag12 = joined.dropna(subset=lag_cols)
    n_post_lag12 = len(post_lag12)
    print(f"\nN raw:           {n_raw}")
    print(f"N post-lag-12:   {n_post_lag12}")
    print(f"N_MIN (spec §3): {N_MIN}")

    if n_post_lag12 < N_MIN:
        raise PairDSampleStructurallyPathological(
            f"N_post_lag_12={n_post_lag12} < N_MIN={N_MIN} — typed exception per "
            f"plan §1.3 Step 2; surface HALT-disposition memo before remediation."
        )
    print(f"GATE PASS: {n_post_lag12} ≥ {N_MIN}")

    # --- Sanity-range Y --------------------------------------------------
    y_broad_mean = float(joined["Y_broad_raw"].mean())
    y_narrow_mean = float(joined["Y_narrow_raw"].mean())
    print(f"\nY_broad_raw  mean={y_broad_mean:.4f} range=[{joined['Y_broad_raw'].min():.4f}, {joined['Y_broad_raw'].max():.4f}] (spec ~0.65)")
    print(f"Y_narrow_raw mean={y_narrow_mean:.4f} range=[{joined['Y_narrow_raw'].min():.4f}, {joined['Y_narrow_raw'].max():.4f}] (spec ~0.09)")

    # --- Persist ---------------------------------------------------------
    final = joined[
        [
            "timestamp_utc",
            "Y_broad_logit",
            "Y_broad_raw",
            "Y_narrow_logit",
            "Y_narrow_raw",
            "log_cop_usd_lag6",
            "log_cop_usd_lag9",
            "log_cop_usd_lag12",
            "n_young_employed",
            "n_young_in_services_broad",
            "n_young_in_services_narrow",
        ]
    ].copy()

    final.to_parquet(OUT, index=False, compression="snappy")
    out_sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"\nWrote: {OUT}")
    print(f"  sha256: {out_sha}")
    print(f"  rows:   {len(final)}")
    print(f"  cols:   {list(final.columns)}")

    # --- Emit summary for orchestrator -----------------------------------
    print("\n=== SUMMARY ===")
    print(f"input_y_broad_sha256  = {fp_broad.sha256}")
    print(f"input_y_narrow_sha256 = {fp_narrow.sha256}")
    print(f"input_x_sha256        = {fp_x.sha256}")
    print(f"output_sha256         = {out_sha}")
    print(f"n_raw                 = {n_raw}")
    print(f"n_post_lag12          = {n_post_lag12}")
    print(f"y_broad_mean          = {y_broad_mean:.4f}")
    print(f"y_narrow_mean         = {y_narrow_mean:.4f}")
    print(f"timestamp_range       = {final['timestamp_utc'].min()} → {final['timestamp_utc'].max()}")


if __name__ == "__main__":
    main()
