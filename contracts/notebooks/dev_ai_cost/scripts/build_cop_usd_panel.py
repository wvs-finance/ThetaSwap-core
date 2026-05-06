"""Build COP/USD lag panel for dev-AI Stage-1 simple-β iteration (Task 1.2).

Spec: contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md
Plan: contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md
Task 1.2 of Phase 1.

Dependent-variable index range: 2015-01 → 2026-03 (135 rows expected).
X back-extension: TRM observations from 2014-01 → 2014-12 are loaded so the
lag-12 column for the 2015-01 row maps onto 2014-01 (per spec §4 v1.0.1
X-back-extension justification + plan Task 1.2 Step 1; SPM FLAG-5 v1.0 closure).

Departure from Pair D convention: Pair D dropped 12 leading Y months
(2015 → 2016-01 start). Dev-AI back-extends X to 2014-01 so Y starts at 2015-01,
preserving the maximum 135-month dependent-variable index. Banrep TRM is
available continuously back to 1991-12; back-extension is mechanically trivial.

Free-tier-only methodology (per spec §9.14, CORRECTIONS-δ inheritance).
Banrep TRM source: datos.gov.co open data API
(https://www.datos.gov.co/resource/32sa-8pi3.json) — no auth, no rate limit.
Cached in DuckDB at contracts/data/structural_econ.duckdb table
banrep_trm_daily, ingested by the closed FX-vol-CPI Phase-A.0 pipeline.

Output: contracts/.scratch/dev-ai-stage-1/data/cop_usd_panel.parquet
Schema: (year_month, log_cop_usd, log_cop_usd_lag6, log_cop_usd_lag9, log_cop_usd_lag12)
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

# Repo-rooted absolute paths (no cwd dependence)
WORKTREE_ROOT = Path("/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom")
DUCKDB_PATH = WORKTREE_ROOT / "contracts" / "data" / "structural_econ.duckdb"
OUT_DIR = WORKTREE_ROOT / "contracts" / ".scratch" / "dev-ai-stage-1" / "data"
OUT_PARQUET = OUT_DIR / "cop_usd_panel.parquet"

# Spec §4 sample-window pin: dependent-variable index 2015-01 → 2026-03 (135 mo).
# X back-extension: load TRM from 2014-01 to fill lag-12.
DEP_START = pd.Timestamp("2015-01-01")
DEP_END = pd.Timestamp("2026-03-01")
X_LOAD_START = pd.Timestamp("2014-01-01")  # 12-month back-extension for lag-12

# Spec §5.2 lag panel: k ∈ {6, 9, 12}.
LAGS = (6, 9, 12)


def fetch_trm_eom() -> pd.DataFrame:
    """Pull Banrep TRM daily from DuckDB, aggregate to end-of-month spot.

    EOM convention (matches spec §5.2 + Pair D §5.2 + closed FX-vol-CPI pipeline):
    "end-of-month spot rate = the LAST AVAILABLE business-day TRM observation
    within each calendar month." Banrep TRM is a business-day series; weekends
    and Colombian holidays are absent. The last published trading day of the
    calendar month is the canonical reference.
    """
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        # Pull continuous daily series 2014-01 → 2026-03 inclusive.
        # Filter is narrow because Banrep TRM only covers business days; we
        # aggregate to month-last observation within each (year, month) cell.
        sql = """
        SELECT date, trm
        FROM banrep_trm_daily
        WHERE date >= DATE '2014-01-01' AND date < DATE '2026-04-01'
        ORDER BY date
        """
        daily = con.execute(sql).df()
    finally:
        con.close()

    if daily.empty:
        raise RuntimeError("Banrep TRM daily query returned zero rows — check DuckDB.")

    # Aggregate to EOM business-day last observation.
    daily["date"] = pd.to_datetime(daily["date"])
    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month
    eom = (
        daily.sort_values("date")
        .groupby(["year", "month"], as_index=False)
        .agg(eom_business_date=("date", "last"), trm_eom=("trm", "last"))
    )
    # Canonical year_month index = first day of month (period stamp).
    eom["year_month"] = pd.to_datetime(
        eom["year"].astype(str) + "-" + eom["month"].astype(str).str.zfill(2) + "-01"
    )
    return eom[["year_month", "eom_business_date", "trm_eom"]].sort_values("year_month").reset_index(drop=True)


def construct_lag_panel(eom: pd.DataFrame) -> pd.DataFrame:
    """Construct the dev-AI panel: dep-var index 2015-01..2026-03; lag panel from X back-extension.

    For each t in [DEP_START, DEP_END]:
        log_cop_usd        = log(TRM_eom_t)
        log_cop_usd_lag6   = log(TRM_eom_{t-6})
        log_cop_usd_lag9   = log(TRM_eom_{t-9})
        log_cop_usd_lag12  = log(TRM_eom_{t-12})

    Lag-12 observations from 2014-01..2014-12 are consumed as regressors but
    the dependent-variable index starts at 2015-01.
    """
    # Sanity check contiguous monthly grid 2014-01..2026-03 (147 cells).
    expected_n = 147
    if len(eom) != expected_n:
        raise RuntimeError(
            f"Expected {expected_n} EOM rows for 2014-01..2026-03; got {len(eom)}. "
            "Possible X-back-extension or coverage gap — HALT per spec §9.5."
        )

    eom = eom.copy()
    eom["log_cop_usd"] = np.log(eom["trm_eom"])

    # Lag panel via positional shift on contiguous monthly grid.
    for k in LAGS:
        eom[f"log_cop_usd_lag{k}"] = eom["log_cop_usd"].shift(k)

    # Restrict to dependent-variable index range. Lag columns at 2015-01 reach
    # back to 2014-01 (lag-12), 2014-04 (lag-9), 2014-07 (lag-6).
    mask = (eom["year_month"] >= DEP_START) & (eom["year_month"] <= DEP_END)
    panel = eom.loc[mask].copy().reset_index(drop=True)

    # Confirm zero NaN in any lag column.
    null_audit = {col: panel[col].isna().sum() for col in panel.columns}
    if any(panel[c].isna().any() for c in ["log_cop_usd"] + [f"log_cop_usd_lag{k}" for k in LAGS]):
        raise RuntimeError(
            f"Unexpected NaN in panel after X-back-extension: {null_audit}. "
            "HALT per spec §9.5 — investigate before emitting parquet."
        )

    # Final schema per plan Task 1.2 Step 3: drop intermediate audit columns.
    out = panel[["year_month", "log_cop_usd", "log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"]].copy()
    return out, panel  # return audit panel for provenance reporting


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[task 1.2] fetching Banrep TRM EOM 2014-01..2026-03 from DuckDB...")
    eom = fetch_trm_eom()
    print(f"  loaded {len(eom)} EOM rows; range [{eom['year_month'].iloc[0].date()} .. {eom['year_month'].iloc[-1].date()}]")
    print(f"  first row: 2014-01-31 EOM TRM = {eom.iloc[0]['trm_eom']:.4f}")
    print(f"  last row:  2026-03-31 EOM TRM = {eom.iloc[-1]['trm_eom']:.4f}")

    print("[task 1.2] constructing lag panel k ∈ {6, 9, 12}...")
    out, audit = construct_lag_panel(eom)
    print(f"  emitted panel rows = {len(out)} (expected 135)")
    print(f"  dep-var index range: {out['year_month'].iloc[0].date()} .. {out['year_month'].iloc[-1].date()}")

    if len(out) != 135:
        raise RuntimeError(f"Realized N = {len(out)} ≠ expected 135. HALT per spec §9.5.")

    # Persist parquet.
    print(f"[task 1.2] writing {OUT_PARQUET} ...")
    out.to_parquet(OUT_PARQUET, index=False)

    # sha256 pin.
    sha = hashlib.sha256(OUT_PARQUET.read_bytes()).hexdigest()
    print(f"  parquet sha256 = {sha}")
    print(f"  parquet bytes  = {OUT_PARQUET.stat().st_size}")

    # Spot-check a few rows for human eyeballing.
    print("[task 1.2] head:")
    print(out.head().to_string())
    print("[task 1.2] tail:")
    print(out.tail().to_string())

    # Emit audit hash to stdout for DATA_PROVENANCE.md inclusion.
    print()
    print(f"PARQUET_SHA256={sha}")
    print(f"PARQUET_BYTES={OUT_PARQUET.stat().st_size}")
    print(f"REALIZED_N={len(out)}")


if __name__ == "__main__":
    main()
