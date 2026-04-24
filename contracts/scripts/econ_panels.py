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
    cpi_surprise_ar1, us_cpi_surprise initialized to 0.0 — Task 6 populates
    CPI surprises via post-processing UPDATE.

    banrep_rate_surprise is constructed directly here via the event-study
    operator of research doc 2026-04-18 §8.1:
        s_w = sum_{τ ∈ meetings ∩ week w} (IBR_ON_τ - IBR_ON_τ-1)
    where τ are Junta Directiva meeting days from ``banrep_meeting_calendar``
    and IBR_ON is the overnight IBR from ``banrep_ibr_daily``. Weeks with no
    meeting receive a structural zero. The within-week SUM handles the rare
    two-meetings-in-one-week case sign-preservingly.
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
    ),
    -- Event-study Banrep surprise (research doc §8.1, Anzoátegui-Zapata &
    -- Galvis 2019 / Uribe-Gil & Galvis-Ciro BIS 2022 canon):
    -- per-meeting-day IBR daily change, SUMMED within week (sign-preserving).
    -- Every row in banrep_meeting_calendar contributes — rate-change meetings
    -- show the full TPM step (~25-100 bp); hold-inferred meetings show OMO
    -- noise (< 5 bp typical per research doc §4.2). This is the literal
    -- spec of §8.1 ("sum over τ in week w of IBR^ON_τ - IBR^ON_τ-1").
    ibr_daily_change AS (
        SELECT
            date AS ibr_date,
            ibr_overnight_er
              - LAG(ibr_overnight_er) OVER (ORDER BY date) AS delta_ibr
        FROM banrep_ibr_daily
    ),
    banrep_surprise_weekly AS (
        SELECT
            date_trunc('week', cal.meeting_date)::DATE AS week_start,
            SUM(COALESCE(idc.delta_ibr, 0.0)) AS banrep_rate_surprise
        FROM banrep_meeting_calendar cal
        LEFT JOIN ibr_daily_change idc ON idc.ibr_date = cal.meeting_date
        GROUP BY date_trunc('week', cal.meeting_date)::DATE
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
        COALESCE(bsw.banrep_rate_surprise, 0.0)::DOUBLE AS banrep_rate_surprise,
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
    LEFT JOIN banrep_surprise_weekly bsw ON bsw.week_start = r.week_start
    ORDER BY r.week_start
    """, [lookback, sample_start, sample_start, lookback])


def build_daily_panel(
    conn: duckdb.DuckDBPyConnection,
    sample_start: date = date(2003, 1, 1),
) -> None:
    """Build daily_panel from raw tables. CREATE OR REPLACE — idempotent.

    One row per COP/USD trading day. Lookback for LAG on first day.
    CPI surprise columns initialized to 0.0 — Task 6 populates via UPDATE.

    banrep_rate_surprise: event-study operator applied at daily frequency —
    on a meeting day the surprise equals the IBR daily change; on non-meeting
    days the surprise is a structural zero (research doc §8.1, §9.3).
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
    ),
    -- Event-study daily surprise (research doc §8.1, §8.4, §9.3): ΔIBR on
    -- every meeting day in banrep_meeting_calendar, structural zero
    -- elsewhere.
    --
    -- Holiday handling (§8.4): when the meeting_date falls on a day with
    -- no FX-trading observation (Colombian TRM does not publish on Lunes
    -- festivo), the surprise is assigned to the first trading day on or
    -- after the meeting date by joining to the trm trading-day index.
    ibr_daily_change AS (
        SELECT
            date AS ibr_date,
            ibr_overnight_er
              - LAG(ibr_overnight_er) OVER (ORDER BY date) AS delta_ibr
        FROM banrep_ibr_daily
    ),
    meeting_with_delta AS (
        SELECT cal.meeting_date,
               COALESCE(idc.delta_ibr, 0.0) AS delta_ibr,
               LEAD(cal.meeting_date) OVER (ORDER BY cal.meeting_date) AS next_meeting
        FROM banrep_meeting_calendar cal
        LEFT JOIN ibr_daily_change idc ON idc.ibr_date = cal.meeting_date
    ),
    banrep_surprise_daily AS (
        SELECT
            MIN(t.date) AS date,
            mwd.delta_ibr AS banrep_rate_surprise
        FROM meeting_with_delta mwd
        JOIN trm_returns t
          ON t.date >= mwd.meeting_date
         AND (mwd.next_meeting IS NULL OR t.date < mwd.next_meeting)
        GROUP BY mwd.meeting_date, mwd.delta_ibr
    )
    SELECT
        t.date,
        t.week_start,
        t.cop_usd_return,
        CAST(0.0 AS DOUBLE) AS abs_cpi_surprise,
        CAST(0.0 AS DOUBLE) AS cpi_surprise_ar1_daily,
        COALESCE(bsd.banrep_rate_surprise, 0.0)::DOUBLE AS banrep_rate_surprise,
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
    LEFT JOIN banrep_surprise_daily bsd ON bsd.date = t.date
    WHERE t.date >= ?
    ORDER BY t.date
    """, [lookback, sample_start])


# ── Task 11.M.6: weekly rate panel (DFF + IBR level) ─────────────────────────
#
# Purely ADDITIVE extension — DOES NOT touch ``weekly_panel``. The Rev-4
# ``weekly_panel`` SHA-256 fingerprint
# (``769ec955e72ddfcb6ff5b16e9c949fd8f53d9e8c349fc56ce96090fce81d791f``)
# is a project-wide invariant asserted by ``test_readme_render`` and the
# NB2/NB3 notebook handoff cells, so this task exposes the new rate
# columns via a separate ``weekly_rate_panel`` VIEW built from the raw
# tables.
#
# Columns:
#   * ``week_start``         Friday-anchored ISO week start (Bogota time
#                             matches US East by weekday; DuckDB
#                             ``date_trunc('week', date)`` yields Monday
#                             so we shift +4 days to land on Friday).
#   * ``fed_funds_weekly``   Friday close of the FRED DFF daily series.
#   * ``banrep_ibr_weekly``  Friday close of banrep_ibr_daily.
#   * ``trm_friday_close``   Friday close of banrep_trm_daily.
#
# Y_asset_leg per RC plan-review is computable downstream as:
#   (banrep_ibr_weekly - fed_funds_weekly) / 52 + trm_return_weekly


def build_weekly_rate_panel(conn: duckdb.DuckDBPyConnection) -> None:
    """Build ``weekly_rate_panel`` VIEW — additive to ``weekly_panel``.

    Friday-anchored weekly closes for DFF, IBR-overnight-ER and TRM. A
    VIEW (not a TABLE) is used so no materialized state competes with
    the Rev-4 fingerprint-locked ``weekly_panel``. Idempotent: uses
    ``CREATE OR REPLACE VIEW``.
    """
    conn.execute("""
    CREATE OR REPLACE VIEW weekly_rate_panel AS
    WITH
    fed_funds_friday AS (
        SELECT date::DATE AS week_start, value AS fed_funds_weekly
        FROM fred_daily
        WHERE series_id = 'DFF'
          AND EXTRACT('isodow' FROM date) = 5
    ),
    ibr_friday AS (
        SELECT date::DATE AS week_start, ibr_overnight_er AS banrep_ibr_weekly
        FROM banrep_ibr_daily
        WHERE EXTRACT('isodow' FROM date) = 5
    ),
    trm_friday AS (
        SELECT date::DATE AS week_start, trm AS trm_friday_close
        FROM banrep_trm_daily
        WHERE EXTRACT('isodow' FROM date) = 5
    )
    SELECT
        COALESCE(ff.week_start, ib.week_start, tf.week_start) AS week_start,
        ff.fed_funds_weekly,
        ib.banrep_ibr_weekly,
        tf.trm_friday_close
    FROM fed_funds_friday ff
    FULL OUTER JOIN ibr_friday ib ON ib.week_start = ff.week_start
    FULL OUTER JOIN trm_friday tf ON tf.week_start
                                   = COALESCE(ff.week_start, ib.week_start)
    WHERE COALESCE(ff.week_start, ib.week_start, tf.week_start) IS NOT NULL
    ORDER BY week_start
    """)


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

    banrep_rate_surprise is NOT handled here — it is constructed directly by
    the event-study operator inside ``build_weekly_panel`` and
    ``build_daily_panel`` (research doc 2026-04-18 §8.1, §9.2, §9.3).
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
