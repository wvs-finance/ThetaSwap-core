"""Panel builders: weekly_panel and daily_panel from raw tables.

SQL computation in DuckDB. Python orchestrates queries and AR(1) post-processing.
"""
from __future__ import annotations

from datetime import date, timedelta as _timedelta
from typing import Final

import duckdb


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
        POWER(r.rv, 1.0/3.0) AS rv_cuberoot,
        LN(r.rv) AS rv_log,
        r.n_trading_days::SMALLINT AS n_trading_days,
        COALESCE(v.vix_avg, 0.0) AS vix_avg,
        v.vix_friday_close,
        COALESCE(o.oil_return, 0.0) AS oil_return,
        o.oil_log_level,
        0.0 AS us_cpi_surprise,
        0.0 AS cpi_surprise_ar1,
        COALESCE(dic.ipc_pct_change, 0.0) AS dane_ipc_pct,
        COALESCE(dip.ipp_pct_change, 0.0) AS dane_ipp_pct,
        0.0 AS banrep_rate_surprise,
        COALESCE(iw.intervention_dummy, 0)::SMALLINT AS intervention_dummy,
        COALESCE(iw.intervention_amount, 0.0) AS intervention_amount,
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
        0.0 AS abs_cpi_surprise,
        0.0 AS cpi_surprise_ar1_daily,
        0.0 AS banrep_rate_surprise,
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
