"""Panel builders: weekly_panel and daily_panel from raw tables.

SQL computation in DuckDB. Python orchestrates queries and AR(1) post-processing.
"""
from __future__ import annotations

from datetime import date, timedelta as _timedelta
from typing import Final

import duckdb
import numpy as np


def build_weekly_panel(
    conn: duckdb.DuckDBPyConnection,
    sample_start: date = date(2003, 1, 6),
) -> None:
    """Build weekly_panel from raw tables. CREATE OR REPLACE — idempotent.

    Uses parameterized queries. Lookback window for LAG() on first sample week.
    dane_ipc_pct/dane_ipp_pct populated from release-week joins.
    cpi_surprise_ar1, us_cpi_surprise, banrep_rate_surprise initialized to 0.0 —
    Task 6 populates CPI surprises via post-processing UPDATE.
    banrep_rate_surprise deferred to estimation module (spec §3.10).
    """
    lookback = sample_start - _timedelta(days=14)
    conn.execute("""
    CREATE OR REPLACE TABLE weekly_panel AS
    WITH
    -- All TRM with log-returns (lookback window for LAG on first sample day)
    trm_returns AS (
        SELECT
            date,
            trm,
            LN(trm / LAG(trm) OVER (ORDER BY date)) AS log_return
        FROM banrep_trm_daily
        WHERE date >= ?
    ),
    -- Assign to weeks, drop NULL returns (first row has no prior price)
    trm_weekly AS (
        SELECT
            date_trunc('week', date)::DATE AS week_start,
            log_return
        FROM trm_returns
        WHERE log_return IS NOT NULL
    ),
    -- RV per week
    rv_agg AS (
        SELECT
            week_start,
            SUM(log_return * log_return) AS rv,
            COUNT(*) AS n_trading_days
        FROM trm_weekly
        WHERE week_start >= ?
        GROUP BY week_start
    ),
    -- VIX weekly: average + last-available (Friday close)
    vix_weekly AS (
        SELECT
            date_trunc('week', date)::DATE AS week_start,
            AVG(value) AS vix_avg,
            ARG_MAX(value, date) AS vix_friday_close
        FROM fred_daily
        WHERE series_id = 'VIXCLS' AND date >= ?
        GROUP BY date_trunc('week', date)::DATE
    ),
    -- Oil: last available price per week (lookback for LAG)
    oil_weekly AS (
        SELECT
            date_trunc('week', date)::DATE AS week_start,
            ARG_MAX(value, date) AS last_oil_price
        FROM fred_daily
        WHERE series_id = 'DCOILWTICO' AND value IS NOT NULL AND date >= ?
        GROUP BY date_trunc('week', date)::DATE
    ),
    oil_with_return AS (
        SELECT
            week_start,
            CASE WHEN last_oil_price > 0 AND LAG(last_oil_price) OVER (ORDER BY week_start) > 0
                 THEN LN(last_oil_price / LAG(last_oil_price) OVER (ORDER BY week_start))
                 ELSE NULL END AS oil_return,
            CASE WHEN last_oil_price > 0 THEN LN(last_oil_price) ELSE NULL END AS oil_log_level
        FROM oil_weekly
    ),
    -- Intervention weekly
    intervention_weekly AS (
        SELECT
            date_trunc('week', date)::DATE AS week_start,
            1 AS intervention_dummy,
            SUM(COALESCE(discretionary, 0) + COALESCE(direct_purchase, 0) +
                COALESCE(put_volatility, 0) + COALESCE(call_volatility, 0) +
                COALESCE(put_reserve_accum, 0) + COALESCE(call_reserve_decum, 0) +
                COALESCE(ndf, 0) + COALESCE(fx_swaps, 0)) AS intervention_amount
        FROM banrep_intervention_daily
        GROUP BY date_trunc('week', date)::DATE
    ),
    -- DANE IPC release-week mapping
    dane_ipc_releases AS (
        SELECT
            date_trunc('week', rc.release_date)::DATE AS week_start,
            dim.ipc_pct_change
        FROM dane_release_calendar rc
        JOIN dane_ipc_monthly dim ON dim.date = make_date(rc.year, rc.month, 1)
        WHERE rc.series = 'ipc'
    ),
    -- DANE IPP release-week mapping
    dane_ipp_releases AS (
        SELECT
            date_trunc('week', rc.release_date)::DATE AS week_start,
            dip.ipp_pct_change
        FROM dane_release_calendar rc
        JOIN dane_ipp_monthly dip ON dip.date = make_date(rc.year, rc.month, 1)
        WHERE rc.series = 'ipp'
    ),
    -- Release-week flags
    cpi_release_weeks AS (
        SELECT DISTINCT date_trunc('week', release_date)::DATE AS week_start
        FROM dane_release_calendar WHERE series = 'ipc'
    ),
    ppi_release_weeks AS (
        SELECT DISTINCT date_trunc('week', release_date)::DATE AS week_start
        FROM dane_release_calendar WHERE series = 'ipp'
    )
    -- Final join (only weeks >= sample_start)
    SELECT
        r.week_start,
        r.rv,
        CASE WHEN r.rv > 0 THEN POWER(r.rv, 1.0/3.0) ELSE 0.0 END AS rv_cuberoot,
        CASE WHEN r.rv > 0 THEN LN(r.rv) ELSE NULL END AS rv_log,
        r.n_trading_days::SMALLINT AS n_trading_days,
        COALESCE(v.vix_avg, 0.0) AS vix_avg,
        v.vix_friday_close,
        COALESCE(o.oil_return, 0.0) AS oil_return,
        o.oil_log_level,
        CAST(0.0 AS DOUBLE) AS us_cpi_surprise,
        CAST(0.0 AS DOUBLE) AS cpi_surprise_ar1,
        COALESCE(dic.ipc_pct_change, 0.0) AS dane_ipc_pct,
        COALESCE(dip.ipp_pct_change, 0.0) AS dane_ipp_pct,
        CAST(0.0 AS DOUBLE) AS banrep_rate_surprise,
        COALESCE(iw.intervention_dummy, 0)::SMALLINT AS intervention_dummy,
        COALESCE(iw.intervention_amount, 0.0)::DOUBLE AS intervention_amount,
        crw.week_start IS NOT NULL AS is_cpi_release_week,
        prw.week_start IS NOT NULL AS is_ppi_release_week
    FROM rv_agg r
    LEFT JOIN vix_weekly v ON v.week_start = r.week_start
    LEFT JOIN oil_with_return o ON o.week_start = r.week_start
    LEFT JOIN intervention_weekly iw ON iw.week_start = r.week_start
    LEFT JOIN dane_ipc_releases dic ON dic.week_start = r.week_start
    LEFT JOIN dane_ipp_releases dip ON dip.week_start = r.week_start
    LEFT JOIN cpi_release_weeks crw ON crw.week_start = r.week_start
    LEFT JOIN ppi_release_weeks prw ON prw.week_start = r.week_start
    ORDER BY r.week_start
    """, [lookback, sample_start, sample_start, lookback])


def build_daily_panel(
    conn: duckdb.DuckDBPyConnection,
    sample_start: date = date(2003, 1, 1),
) -> None:
    """Build daily_panel from raw tables. CREATE OR REPLACE — idempotent.

    One row per COP/USD trading day. Lookback for LAG on first day.
    Surprise columns initialized to 0.0 — Task 6 populates via UPDATE.
    """
    lookback = sample_start - _timedelta(days=14)
    conn.execute("""
    CREATE OR REPLACE TABLE daily_panel AS
    WITH
    trm_returns AS (
        SELECT
            date,
            date_trunc('week', date)::DATE AS week_start,
            LN(trm / LAG(trm) OVER (ORDER BY date)) AS cop_usd_return
        FROM banrep_trm_daily
        WHERE date >= ?
    ),
    cpi_release_days AS (
        SELECT release_date AS date FROM dane_release_calendar WHERE series = 'ipc'
    ),
    ppi_release_days AS (
        SELECT release_date AS date FROM dane_release_calendar WHERE series = 'ipp'
    ),
    oil_returns AS (
        SELECT
            date,
            CASE WHEN value > 0 AND LAG(value) OVER (ORDER BY date) > 0
                 THEN LN(value / LAG(value) OVER (ORDER BY date))
                 ELSE NULL END AS oil_return,
            CASE WHEN value > 0 THEN LN(value) ELSE NULL END AS oil_log_level
        FROM fred_daily
        WHERE series_id = 'DCOILWTICO' AND value IS NOT NULL
    )
    SELECT
        t.date,
        t.week_start,
        t.cop_usd_return,
        CAST(0.0 AS DOUBLE) AS abs_cpi_surprise,
        CAST(0.0 AS DOUBLE) AS cpi_surprise_ar1_daily,
        CAST(0.0 AS DOUBLE) AS banrep_rate_surprise,
        CASE WHEN bi.date IS NOT NULL THEN 1 ELSE 0 END::SMALLINT AS intervention_dummy,
        v.value AS vix,
        o.oil_return,
        o.oil_log_level,
        cd.date IS NOT NULL AS is_cpi_release_day,
        pd.date IS NOT NULL AS is_ppi_release_day
    FROM trm_returns t
    LEFT JOIN fred_daily v ON v.series_id = 'VIXCLS' AND v.date = t.date
    LEFT JOIN oil_returns o ON o.date = t.date
    LEFT JOIN banrep_intervention_daily bi ON bi.date = t.date
    LEFT JOIN cpi_release_days cd ON cd.date = t.date
    LEFT JOIN ppi_release_days pd ON pd.date = t.date
    WHERE t.date >= ?
    ORDER BY t.date
    """, [lookback, sample_start])


# ── AR(1) surprise construction ──────────────────────────────────────────────


def _ar1_expanding_surprises(
    pct_changes: list[float],
    warmup: int,
) -> list[float | None]:
    """Compute expanding-window AR(1) surprises.

    Returns a list parallel to pct_changes. Indices < warmup are None.
    surprise[t] = actual[t] - (a + b * actual[t-1]) where a,b fit on [0..t-1].
    """
    result: list[float | None] = [None] * len(pct_changes)
    for t in range(warmup, len(pct_changes)):
        y = np.array(pct_changes[:t])
        if len(y) < 2:
            continue
        y_lag = y[:-1]
        y_curr = y[1:]
        x_mat = np.column_stack([np.ones(len(y_lag)), y_lag])
        try:
            coeffs = np.linalg.lstsq(x_mat, y_curr, rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        forecast = coeffs[0] + coeffs[1] * pct_changes[t - 1]
        result[t] = pct_changes[t] - forecast
    return result


def compute_ar1_surprises(
    conn: duckdb.DuckDBPyConnection,
    warmup_months: int = 12,
) -> None:
    """Compute AR(1) CPI surprises and update weekly_panel + daily_panel.

    Colombian CPI: expanding-window AR(1) on DANE IPC MoM % changes.
    US CPI: same method on CPIAUCSL MoM % changes.
    Mapped to release weeks/days via calendars.
    banrep_rate_surprise deferred to estimation module (spec §3.10).
    """
    # Check which panels exist
    existing_tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    has_weekly = "weekly_panel" in existing_tables
    has_daily = "daily_panel" in existing_tables

    # ── Colombian CPI AR(1) ──
    ipc_rows = conn.execute(
        "SELECT date, ipc_pct_change FROM dane_ipc_monthly ORDER BY date"
    ).fetchall()

    if len(ipc_rows) >= warmup_months + 1:
        pct_changes = [float(r[1]) for r in ipc_rows]
        ipc_dates = [r[0] for r in ipc_rows]
        surprises = _ar1_expanding_surprises(pct_changes, warmup_months)

        # Fetch IPC release calendar
        release_map: dict[tuple[int, int], date] = {}
        for yr, mo, rd in conn.execute(
            "SELECT year, month, release_date FROM dane_release_calendar WHERE series = 'ipc'"
        ).fetchall():
            release_map[(yr, mo)] = rd

        for t in range(warmup_months, len(pct_changes)):
            s = surprises[t]
            if s is None:
                continue
            ref_date = ipc_dates[t]
            release_date = release_map.get((ref_date.year, ref_date.month))
            if release_date is None:
                continue

            # Update weekly_panel
            if has_weekly:
                week_start = conn.execute(
                    "SELECT date_trunc('week', ?::DATE)::DATE", [release_date]
                ).fetchone()
                if week_start is not None:
                    conn.execute(
                        "UPDATE weekly_panel SET cpi_surprise_ar1 = ? WHERE week_start = ?",
                        [s, week_start[0]],
                    )

            # Update daily_panel
            if has_daily:
                conn.execute(
                    "UPDATE daily_panel SET cpi_surprise_ar1_daily = ?, abs_cpi_surprise = ? WHERE date = ?",
                    [s, abs(s), release_date],
                )

    # ── US CPI AR(1) ──
    us_cpi_rows = conn.execute(
        "SELECT date, value FROM fred_monthly WHERE series_id = 'CPIAUCSL' ORDER BY date"
    ).fetchall()

    if len(us_cpi_rows) >= 2:
        us_values = [float(r[1]) for r in us_cpi_rows if r[1] is not None]
        us_dates = [r[0] for r in us_cpi_rows if r[1] is not None]

        # Compute MoM % changes
        us_pct = [(us_values[i] / us_values[i - 1] - 1) * 100 for i in range(1, len(us_values))]
        us_pct_dates = us_dates[1:]

        if len(us_pct) >= warmup_months + 1:
            us_surprises = _ar1_expanding_surprises(us_pct, warmup_months)

            # BLS release calendar
            bls_map: dict[tuple[int, int], date] = {}
            for yr, mo, rd in conn.execute(
                "SELECT year, month, release_date FROM bls_release_calendar"
            ).fetchall():
                bls_map[(yr, mo)] = rd

            for t in range(warmup_months, len(us_pct)):
                s = us_surprises[t]
                if s is None:
                    continue
                ref_date = us_pct_dates[t]
                ref_key = (ref_date.year, ref_date.month)
                release_date = bls_map.get(ref_key)
                if release_date is None:
                    continue

                if has_weekly:
                    week_start = conn.execute(
                        "SELECT date_trunc('week', ?::DATE)::DATE", [release_date]
                    ).fetchone()
                    if week_start is not None:
                        conn.execute(
                            "UPDATE weekly_panel SET us_cpi_surprise = ? WHERE week_start = ?",
                            [s, week_start[0]],
                        )
