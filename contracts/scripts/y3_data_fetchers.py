"""Y₃ inequality-differential data fetchers — Rev-5.3.1 Task 11.N.2d.

Pure free functions (no mutation, no global state — only HTTP I/O).
Per design doc §8 contract:

    fetch_country_equity(country, start, end) -> pd.DataFrame
    fetch_country_sovereign_yield(country, start, end) -> pd.DataFrame
    fetch_country_wc_cpi_components(country, start, end) -> pd.DataFrame

Data sources per design doc §3 / §4 / §10 row 1 (Kenya bottleneck):

* Equity indices via Yahoo Finance ``query1.finance.yahoo.com/v8/finance/chart``
  (free, no API key, daily bars). Tickers:
    CO: ICOLCAP.CL (iColcap ETF, follows COLCAP)
    BR: ^BVSP (IBOVESPA)
    EU: ^STOXX (STOXX 600)
    KE: not on Yahoo at consistent cadence — falls back per §10 row 1.

* WC-CPI components via DBnomics public REST API (no auth):
    EU full split: Eurostat ``prc_hicp_midx`` — COICOP CP01 (food),
        CP045 (electricity / energy), CP04 (housing), CP07 (transport).
    CO/BR/KE: IMF IFS ``M.{country}.PCPI_IX`` headline-only —
        per §10 row 2 substitution-fallback rule, all four component
        columns are populated with the headline-CPI level. The 60/25/15
        weighted composite then collapses to headline level for those
        countries — well-defined and monthly-cadence-faithful.

* Sovereign yields: not consumed by the primary panel construction
  (design doc §3 marks bond yield as DIAGNOSTIC, not primary). Fetcher
  exists for the design-doc §8 I/O contract but is currently a no-op
  placeholder that raises :class:`Y3FetchError` for KE.

All fetchers raise :class:`Y3FetchError` on persistent HTTP failure or
empty payload — the caller (``scripts.econ_pipeline.ingest_y3_weekly``)
catches per-country failures and routes through the design-doc §10
graceful-degradation paths (3-country aggregate fallback).
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Final, Literal

import pandas as pd
import requests

if TYPE_CHECKING:
    import duckdb

CountryCode = Literal["CO", "BR", "KE", "EU"]

ALL_COUNTRIES: Final[tuple[CountryCode, ...]] = ("CO", "BR", "KE", "EU")


# ── Yahoo Finance equity-index tickers (no API key required) ────────────────
# Yahoo's ``v8/finance/chart`` endpoint accepts a User-Agent header and
# returns JSON daily-bar data without authentication.

_YAHOO_EQUITY_TICKERS: Final[dict[str, str | None]] = {
    "CO": "ICOLCAP.CL",  # iShares COLCAP ETF, intraday-following the COLCAP
    "BR": "^BVSP",        # IBOVESPA
    "KE": None,            # NSE 20 not on Yahoo; falls back per §10 row 1
    "EU": "^STOXX",       # STOXX 600
}

_YAHOO_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (X11; Linux x86_64) AbrigoY3DataFetcher/1.0"
)


# ── DBnomics CPI series IDs ─────────────────────────────────────────────────
# Public REST API at https://api.db.nomics.world/v22/series/{provider/dataset/code}
# Free, no auth.

# IMF IFS headline CPI (monthly index, M.{country}.PCPI_IX)
_DBNOMICS_HEADLINE_CPI: Final[dict[str, str | None]] = {
    "CO": "IMF/IFS/M.CO.PCPI_IX",
    "BR": "IMF/IFS/M.BR.PCPI_IX",
    "KE": "IMF/IFS/M.KE.PCPI_IX",
    "EU": None,  # Eurozone headline via Eurostat split below
}

# Eurostat HICP COICOP-2 split (Eurozone EA20)
_DBNOMICS_EU_HICP: Final[dict[str, str]] = {
    "food": "Eurostat/prc_hicp_midx/M.I15.CP01.EA20",
    "energy": "Eurostat/prc_hicp_midx/M.I15.CP045.EA20",  # electricity, gas, fuels
    "housing": "Eurostat/prc_hicp_midx/M.I15.CP04.EA20",  # housing/water/electricity
    "transport": "Eurostat/prc_hicp_midx/M.I15.CP07.EA20",
    "headline": "Eurostat/prc_hicp_midx/M.I15.CP00.EA20",
}


class Y3FetchError(RuntimeError):
    """Raised when an external data fetch fails persistently or returns empty."""


# ── HTTP helpers ────────────────────────────────────────────────────────────


def _http_get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict:
    """Pure-HTTP GET with JSON parse. Raises :class:`Y3FetchError` on failure."""
    try:
        resp = requests.get(url, headers=headers or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise Y3FetchError(f"HTTP/JSON failed for {url}: {exc}") from exc


def _dbnomics_fetch_monthly(
    series_path: str,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Fetch a single DBnomics monthly series and return a tidy DataFrame.

    Output columns: ``date`` (DATE, first-of-month), ``value`` (DOUBLE).
    """
    url = f"https://api.db.nomics.world/v22/series/{series_path}?observations=1"
    j = _http_get_json(url)
    docs = j.get("series", {}).get("docs", [])
    if not docs:
        raise Y3FetchError(f"DBnomics {series_path} returned empty docs")
    periods = docs[0].get("period", [])
    values = docs[0].get("value", [])
    rows: list[dict] = []
    for p, v in zip(periods, values, strict=True):
        if v is None:
            continue
        # period format: 'YYYY-MM' — first-of-month timestamp.
        try:
            d = datetime.strptime(p, "%Y-%m").date()
        except ValueError:
            try:
                d = datetime.strptime(p, "%Y-%m-%d").date()
            except ValueError:
                continue
        if start <= d <= end:
            rows.append({"date": d, "value": float(v)})
    if not rows:
        raise Y3FetchError(
            f"DBnomics {series_path}: no rows in [{start}, {end}]"
        )
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def _yahoo_fetch_chart(
    ticker: str,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Fetch daily-close bars via Yahoo Finance chart endpoint.

    Output columns: ``date`` (DATE), ``equity_close`` (DOUBLE).
    """
    p1 = int(datetime(start.year, start.month, start.day).timestamp())
    # End-exclusive in Yahoo; pad by 1 day.
    p2 = int(datetime(end.year, end.month, end.day).timestamp()) + 86400
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{ticker}?period1={p1}&period2={p2}&interval=1d"
    )
    j = _http_get_json(url, headers={"User-Agent": _YAHOO_USER_AGENT})
    chart = j.get("chart", {})
    err = chart.get("error")
    if err:
        raise Y3FetchError(f"Yahoo {ticker} error: {err}")
    result = chart.get("result", []) or []
    if not result:
        raise Y3FetchError(f"Yahoo {ticker} returned no result")
    r = result[0]
    timestamps = r.get("timestamp", []) or []
    quote_blk = r.get("indicators", {}).get("quote", [{}])[0]
    closes = quote_blk.get("close", []) or []
    rows: list[dict] = []
    for ts, c in zip(timestamps, closes, strict=True):
        if c is None or ts is None:
            continue
        d = datetime.fromtimestamp(ts).date()
        if start <= d <= end:
            rows.append({"date": d, "equity_close": float(c)})
    if not rows:
        raise Y3FetchError(
            f"Yahoo {ticker}: no rows in [{start}, {end}]"
        )
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


# ── Public fetchers (per design doc §8 I/O contract) ───────────────────────


def fetch_country_equity(
    country: CountryCode,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Daily-close equity-index series for ``country`` over ``[start, end]``.

    Output columns:
        date          : DATE
        equity_close  : DOUBLE (daily close in country-native currency)

    Source: Yahoo Finance ``v8/finance/chart`` endpoint (free, no key).
    Raises :class:`Y3FetchError` for Kenya (``country == "KE"``) — the
    NSE 20 is not on Yahoo at consistent cadence; the design doc §10
    row 1 recovery protocol delegates Kenya-fallback to the caller.
    """
    ticker = _YAHOO_EQUITY_TICKERS[country]
    if ticker is None:
        raise Y3FetchError(
            f"No Yahoo equity ticker configured for {country}; "
            "delegating to design-doc §10 row 1 fallback"
        )
    return _yahoo_fetch_chart(ticker, start, end)


def fetch_country_sovereign_yield(
    country: CountryCode,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Monthly sovereign 10Y yield for ``country`` over ``[start, end]``.

    Output columns (per design doc §8 contract):
        date         : DATE (monthly)
        yield_pct    : DOUBLE (long-term yield, percent per annum)

    Per design doc §3, sovereign-bond yield is DIAGNOSTIC, not primary.
    This fetcher is exposed for the §8 I/O contract but is not consumed
    by the primary-panel ingestion path; it raises a documented
    :class:`Y3FetchError` placeholder until a consistent free-tier
    source is wired in for all 4 countries.
    """
    raise Y3FetchError(
        f"sovereign-yield fetch not consumed by primary panel for {country}; "
        "design-doc §3 marks bond yield DIAGNOSTIC, not primary"
    )


def fetch_country_wc_cpi_components(
    country: CountryCode,
    start: date,
    end: date,
    *,
    conn: "duckdb.DuckDBPyConnection | None" = None,
) -> pd.DataFrame:
    """Monthly CPI component levels (food / energy / housing / transport).

    Output columns (per design doc §8 contract):
        date          : DATE (monthly, first-of-month)
        food_cpi      : DOUBLE
        energy_cpi    : DOUBLE
        housing_cpi   : DOUBLE
        transport_cpi : DOUBLE

    Source-routing:
      * EU: Eurostat HICP via DBnomics — full COICOP-2 split available.
      * CO (Rev-5.3.2 Task 11.N.2.CO-dane-wire): when ``conn`` is provided,
        consume the existing-and-populated ``dane_ipc_monthly`` DuckDB
        table directly (DANE source, ≤ 2-month staleness). When ``conn``
        is None, fall back to the IMF-IFS-via-DBnomics path — preserved
        as the single-source-IMF-only sensitivity comparator consumed by
        Task 11.N.2d.1-reframe.
      * BR (Rev-5.3.2 Task 11.N.2.BR-bcb-fetcher): when ``conn`` is
        provided, consume the ``bcb_ipca_monthly`` DuckDB table
        (BCB SGS/433 cumulative-index materialization, ≤ 2-month
        staleness). When ``conn`` is None, fall back to the
        IMF-IFS-via-DBnomics path — preserved byte-exact as the
        single-source-IMF-only sensitivity comparator consumed by
        Task 11.N.2d.1-reframe.
      * KE: IMF IFS headline CPI via DBnomics — split components
        are not consistently published on free-tier APIs at monthly
        cadence for KE; per design doc §10 row 2 substitution-fallback
        rule, the headline level is broadcast across all four component
        columns. The 60/25/15 weighted composite then collapses to the
        headline level for KE — a well-defined monthly inflation series
        whose log-changes drive the per-country differential.

    The ``conn`` kwarg is opt-in and country-conditional: only the CO
    and BR branches consume it under Rev-5.3.2. Other branches (EU, KE)
    ignore it, preserving backward compatibility for callers that pre-
    date the DANE / BCB wire-ups. The ``dane_ipc_monthly`` table is
    read-only; the ``bcb_ipca_monthly`` table is populated by
    :func:`scripts.econ_pipeline.ingest_bcb_ipca_monthly` (consume-only
    here — this fetcher does not re-ingest).

    Raises :class:`Y3FetchError` when the fetch fails or returns no rows.
    """
    if country == "EU":
        return _fetch_eu_hicp_split(start, end)
    if country == "CO" and conn is not None:
        return _fetch_dane_headline_broadcast(conn, start, end)
    if country == "BR" and conn is not None:
        return _fetch_bcb_headline_broadcast(conn, start, end)
    return _fetch_imf_ifs_headline_broadcast(country, start, end)


def _fetch_eu_hicp_split(start: date, end: date) -> pd.DataFrame:
    """Eurostat HICP monthly components for the Eurozone (EA20)."""
    food = _dbnomics_fetch_monthly(
        _DBNOMICS_EU_HICP["food"], start, end
    ).rename(columns={"value": "food_cpi"})
    energy = _dbnomics_fetch_monthly(
        _DBNOMICS_EU_HICP["energy"], start, end
    ).rename(columns={"value": "energy_cpi"})
    housing = _dbnomics_fetch_monthly(
        _DBNOMICS_EU_HICP["housing"], start, end
    ).rename(columns={"value": "housing_cpi"})
    transport = _dbnomics_fetch_monthly(
        _DBNOMICS_EU_HICP["transport"], start, end
    ).rename(columns={"value": "transport_cpi"})

    out = (
        food.merge(energy, on="date", how="outer")
        .merge(housing, on="date", how="outer")
        .merge(transport, on="date", how="outer")
        .sort_values("date")
        .reset_index(drop=True)
    )
    out = out.dropna(
        subset=["food_cpi", "energy_cpi", "housing_cpi", "transport_cpi"],
        how="any",
    ).reset_index(drop=True)
    if out.empty:
        raise Y3FetchError(
            f"EU HICP components empty in [{start}, {end}]"
        )
    return out


def _fetch_imf_ifs_headline_broadcast(
    country: CountryCode,
    start: date,
    end: date,
) -> pd.DataFrame:
    """IMF IFS headline CPI broadcast across the 4 component columns.

    Substitution-fallback per design doc §10 row 2: when split
    components are unavailable on free-tier APIs, the headline level
    populates every component slot. The 60/25/15 weights then collapse
    to ``1.00 × headline_level``, but the resulting WC-CPI series is
    still a well-defined monthly inflation level whose Δlog drives the
    per-country differential per design doc §1.
    """
    series = _DBNOMICS_HEADLINE_CPI[country]
    if series is None:
        raise Y3FetchError(
            f"No IMF IFS series configured for {country}"
        )
    headline = _dbnomics_fetch_monthly(series, start, end)
    return pd.DataFrame(
        {
            "date": headline["date"],
            "food_cpi": headline["value"],
            "energy_cpi": headline["value"],
            "housing_cpi": headline["value"],
            "transport_cpi": headline["value"],
        }
    )


def _fetch_dane_headline_broadcast(
    conn: "duckdb.DuckDBPyConnection",
    start: date,
    end: date,
) -> pd.DataFrame:
    """DANE IPC headline level broadcast across the 4 component columns.

    Rev-5.3.2 Task 11.N.2.CO-dane-wire: the CO branch of
    :func:`fetch_country_wc_cpi_components` consumes the existing-and-
    populated ``dane_ipc_monthly`` DuckDB table via the canonical
    :func:`scripts.econ_query_api.load_dane_ipc_monthly` reader (consume-
    only — no schema mutation, no re-ingestion).

    DANE publishes a headline IPC index only (no expenditure-component
    split at the monthly cadence); per design doc §10 row 2 substitution-
    fallback rule, the headline level is broadcast across all four
    component slots. The 60/25/15 weighted composite then collapses to
    the headline level for CO — a well-defined monthly inflation level
    whose Δlog drives the per-country differential per design doc §1.

    Same broadcast contract as :func:`_fetch_imf_ifs_headline_broadcast`;
    same DataFrame shape — the consumer contract is preserved byte-exact.
    """
    # Local import to avoid a circular import at module-load time
    # (econ_query_api is consumer-side state; y3_data_fetchers is HTTP).
    from scripts.econ_query_api import load_dane_ipc_monthly

    rows = load_dane_ipc_monthly(conn, start=start, end=end)
    if not rows:
        raise Y3FetchError(
            f"DANE ipc table: no rows in [{start}, {end}]"
        )
    levels = [r.ipc_index for r in rows]
    dates = [r.date for r in rows]
    return pd.DataFrame(
        {
            "date": dates,
            "food_cpi": levels,
            "energy_cpi": levels,
            "housing_cpi": levels,
            "transport_cpi": levels,
        }
    )


def _fetch_bcb_headline_broadcast(
    conn: "duckdb.DuckDBPyConnection",
    start: date,
    end: date,
) -> pd.DataFrame:
    """BCB IPCA cumulative-index level broadcast across the 4 component columns.

    Rev-5.3.2 Task 11.N.2.BR-bcb-fetcher: the BR branch of
    :func:`fetch_country_wc_cpi_components` consumes the
    ``bcb_ipca_monthly`` DuckDB table (populated by
    :func:`scripts.econ_pipeline.ingest_bcb_ipca_monthly`) via the
    canonical :func:`scripts.econ_query_api.load_bcb_ipca_monthly` reader.
    Consume-only here — the fetcher does NOT re-ingest; the caller is
    responsible for ensuring the table is current via the ingest
    function before invoking this dispatch.

    BCB SGS/433 publishes a headline IPCA monthly variation only (no
    expenditure-component split at the monthly cadence on the free-tier
    direct API); per design doc §10 row 2 substitution-fallback rule,
    the materialized cumulative-index level is broadcast across all four
    component slots. The 60/25/15 weighted composite then collapses to
    the headline cumulative-index level for BR — a well-defined monthly
    level series whose Δlog drives the per-country differential per
    design doc §1.

    Same broadcast contract as :func:`_fetch_imf_ifs_headline_broadcast`
    and :func:`_fetch_dane_headline_broadcast`; same DataFrame shape —
    the consumer contract is preserved byte-exact.
    """
    # Local import avoids a circular import at module-load time
    # (econ_query_api is consumer-side state; y3_data_fetchers is HTTP).
    from scripts.econ_query_api import load_bcb_ipca_monthly

    rows = load_bcb_ipca_monthly(conn, start=start, end=end)
    if not rows:
        raise Y3FetchError(
            f"BCB ipca table: no rows in [{start}, {end}]"
        )
    levels = [r.ipca_index_cumulative for r in rows]
    dates = [r.date for r in rows]
    return pd.DataFrame(
        {
            "date": dates,
            "food_cpi": levels,
            "energy_cpi": levels,
            "housing_cpi": levels,
            "transport_cpi": levels,
        }
    )
