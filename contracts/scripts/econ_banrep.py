"""BanRep data fetchers: TRM (Socrata), IBR (SDMX), intervention (cached JSON).

Pure functions — no side effects except HTTP when explicitly called.
"""
from __future__ import annotations

import json as _json
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Final
from xml.etree import ElementTree

import requests


# ── Domain types ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TrmRow:
    """One daily TRM observation."""
    date: date
    trm: float


@dataclass(frozen=True, slots=True)
class IbrRow:
    """One daily IBR overnight effective rate observation."""
    date: date
    ibr_overnight_er: float


@dataclass(frozen=True, slots=True)
class InterventionRow:
    """One daily FX intervention record."""
    date: date
    discretionary: float | None
    direct_purchase: float | None
    put_volatility: float | None
    call_volatility: float | None
    put_reserve_accum: float | None
    call_reserve_decum: float | None
    ndf: float | None
    fx_swaps: float | None


@dataclass(frozen=True, slots=True)
class TpmRow:
    """One daily TPM (Central Bank Rate / Tasa de Política Monetaria) observation.

    Sourced from Banrep's DF_CBR_DAILY_HIST SDMX dataflow. The TPM is a step
    function: it only changes on Junta Directiva monetary-policy decision days.
    A non-zero value of ``tpm - LAG(tpm)`` is therefore a sufficient (though
    not necessary) signature of a Junta rate-decision meeting day.
    """
    date: date
    tpm: float


@dataclass(frozen=True, slots=True)
class MeetingRow:
    """One Banrep Junta Directiva meeting, filtered to monetary-policy events."""
    year: int
    meeting_date: date
    meeting_type: str


# ── TRM (Socrata) ───────────────────────────────────────────────────────────

_TRM_ENDPOINT: Final[str] = "https://www.datos.gov.co/resource/32sa-8pi3.json"


def parse_trm_socrata_response(data: list[dict[str, str]]) -> list[TrmRow]:
    """Parse Socrata JSON response into TrmRow list.

    Socrata returns valor as string, vigenciadesde with T00:00:00.000 suffix.
    """
    rows: list[TrmRow] = []
    for record in data:
        valor_str = record.get("valor", "")
        fecha_str = record.get("vigenciadesde", "")
        if not valor_str or not fecha_str:
            continue
        parsed_date = datetime.fromisoformat(fecha_str).date()
        rows.append(TrmRow(date=parsed_date, trm=float(valor_str)))
    return rows


def fetch_trm(limit: int = 50000) -> list[TrmRow]:
    """Fetch full TRM history from Datos Abiertos Socrata API.

    Sets $limit to avoid silent truncation (Socrata default = 1000).
    """
    resp = requests.get(_TRM_ENDPOINT, params={"$limit": limit}, timeout=60)
    resp.raise_for_status()
    return parse_trm_socrata_response(resp.json())


# ── IBR (SDMX XML) ──────────────────────────────────────────────────────────

_IBR_ENDPOINT: Final[str] = (
    "https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/"
    "ESTAT,DF_IBR_DAILY_HIST,1.0/all/ALL/"
)

_SDMX_GEN_NS: Final[str] = "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"


def parse_ibr_sdmx_xml(xml_text: str) -> list[IbrRow]:
    """Parse SDMX-ML Generic Data XML for IBR overnight effective rate.

    Filters for SUBJECT=IRIBRM00 (overnight), UNIT_MEASURE=ER (effective).
    """
    root = ElementTree.fromstring(xml_text)
    rows: list[IbrRow] = []

    for series in root.iter(f"{{{_SDMX_GEN_NS}}}Series"):
        # Extract dimensions from SeriesKey
        dims: dict[str, str] = {}
        series_key = series.find(f"{{{_SDMX_GEN_NS}}}SeriesKey")
        if series_key is not None:
            for val_el in series_key.findall(f"{{{_SDMX_GEN_NS}}}Value"):
                dim_id = val_el.get("id", "")
                dim_val = val_el.get("value", "")
                dims[dim_id] = dim_val

        if dims.get("SUBJECT") != "IRIBRM00" or dims.get("UNIT_MEASURE") != "ER":
            continue

        for obs in series.findall(f"{{{_SDMX_GEN_NS}}}Obs"):
            obs_dim = obs.find(f"{{{_SDMX_GEN_NS}}}ObsDimension")
            obs_val = obs.find(f"{{{_SDMX_GEN_NS}}}ObsValue")
            if obs_dim is None or obs_val is None:
                continue

            date_str = obs_dim.get("value", "")
            value_str = obs_val.get("value", "")
            if not date_str or not value_str:
                continue

            parsed_date = datetime.strptime(date_str, "%Y%m%d").date()
            rows.append(IbrRow(date=parsed_date, ibr_overnight_er=float(value_str)))

    return rows


def fetch_ibr(start_year: int = 2008, end_year: int = 2027) -> list[IbrRow]:
    """Fetch IBR overnight history from BanRep SDMX REST API.

    endPeriod is exclusive on year — set end_year = current_year + 1.
    """
    params = {
        "startPeriod": str(start_year),
        "endPeriod": str(end_year),
        "dimensionAtObservation": "TIME_PERIOD",
        "detail": "full",
    }
    headers = {"Accept": "application/vnd.sdmx.genericdata+xml;version=2.1"}
    resp = requests.get(_IBR_ENDPOINT, params=params, headers=headers, timeout=120)
    resp.raise_for_status()
    return parse_ibr_sdmx_xml(resp.text)


# ── TPM (Central Bank Rate / Tasa de Política Monetaria, SDMX XML) ──────────

_TPM_ENDPOINT: Final[str] = (
    "https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/"
    "ESTAT,DF_CBR_DAILY_HIST,1.0/all/ALL/"
)


def parse_tpm_sdmx_xml(xml_text: str) -> list[TpmRow]:
    """Parse SDMX-ML Generic Data XML for the TPM daily historical series.

    Filters SUBJECT=IRCBRM01 (Central Bank Rate), UNIT_MEASURE=PA (per annum,
    percent). The series is a step function: each observation repeats the
    prior day's rate except on Junta Directiva decision days.
    """
    root = ElementTree.fromstring(xml_text)
    rows: list[TpmRow] = []

    for series in root.iter(f"{{{_SDMX_GEN_NS}}}Series"):
        dims: dict[str, str] = {}
        series_key = series.find(f"{{{_SDMX_GEN_NS}}}SeriesKey")
        if series_key is not None:
            for val_el in series_key.findall(f"{{{_SDMX_GEN_NS}}}Value"):
                dim_id = val_el.get("id", "")
                dim_val = val_el.get("value", "")
                dims[dim_id] = dim_val

        if dims.get("SUBJECT") != "IRCBRM01" or dims.get("UNIT_MEASURE") != "PA":
            continue

        for obs in series.findall(f"{{{_SDMX_GEN_NS}}}Obs"):
            obs_dim = obs.find(f"{{{_SDMX_GEN_NS}}}ObsDimension")
            obs_val = obs.find(f"{{{_SDMX_GEN_NS}}}ObsValue")
            if obs_dim is None or obs_val is None:
                continue

            date_str = obs_dim.get("value", "")
            value_str = obs_val.get("value", "")
            if not date_str or not value_str:
                continue

            parsed_date = datetime.strptime(date_str, "%Y%m%d").date()
            rows.append(TpmRow(date=parsed_date, tpm=float(value_str)))

    rows.sort(key=lambda r: r.date)
    return rows


def fetch_tpm(start_year: int = 2008, end_year: int = 2027) -> list[TpmRow]:
    """Fetch TPM daily historical series from Banrep SDMX REST API."""
    params = {
        "startPeriod": str(start_year),
        "endPeriod": str(end_year),
        "dimensionAtObservation": "TIME_PERIOD",
        "detail": "full",
    }
    headers = {"Accept": "application/vnd.sdmx.genericdata+xml;version=2.1"}
    resp = requests.get(_TPM_ENDPOINT, params=params, headers=headers, timeout=120)
    resp.raise_for_status()
    return parse_tpm_sdmx_xml(resp.text)


def derive_meetings_from_tpm(tpm_rows: list[TpmRow]) -> list[MeetingRow]:
    """Identify Junta Directiva rate-decision meeting days from TPM series.

    A meeting day is any date where the TPM level differs from the prior
    non-null observation. This captures every **rate-change** meeting over
    the series window — the authoritative, publicly verifiable subset. The
    ``meeting_date`` stored here is the *effective date* (the first trading
    day on which the new TPM applies), which is also the day the IBR
    overnight rate steps to the new level via Banrep's daily IBR-TPM
    reconciliation adjustment (research doc 2026-04-18 §4.1, §4.3).

    Hold (no-change) meetings are not derivable from the TPM series alone;
    they must be supplemented externally — see ``derive_hold_meetings``.

    Pure function — takes parsed rows, returns MeetingRow list.
    """
    if not tpm_rows:
        return []

    meetings: list[MeetingRow] = []
    prior_tpm = tpm_rows[0].tpm
    for row in tpm_rows[1:]:
        if row.tpm != prior_tpm:
            meetings.append(MeetingRow(
                year=row.date.year,
                meeting_date=row.date,
                meeting_type="policy_rate_decision",
            ))
        prior_tpm = row.tpm
    return meetings


# Banrep Junta Directiva institutional cadence (research doc §5.1, §7.1):
#   • 2008-2012: monthly (last Friday of every calendar month, ~12/year)
#   • 2013-present: 8 scheduled rate decisions per year (Jan, Mar, Apr, Jun,
#     Jul, Sep, Oct, Dec — last Friday of each listed month)
# Source: Banrep published annual schedules; modal pattern confirmed by
# observing the 89 TPM-change effective dates (post-meeting Monday).
#
# This is an *institutional cadence model*, not a scraped record — it is
# the research doc's §5.2 Path-B fallback applied in a controlled way to
# generate hold-meeting dates only. Rate-change meetings always come from
# the TPM series (Path A, authoritative) and override any inferred entry
# for the same week via INSERT OR REPLACE.

_MONTHLY_MEETING_YEARS: Final[range] = range(2008, 2013)
_EIGHT_PER_YEAR_MEETING_MONTHS: Final[tuple[int, ...]] = (1, 3, 4, 6, 7, 9, 10, 12)


def _last_friday_of_month(year: int, month: int) -> date:
    """Return the last Friday of the given year/month."""
    last_day = date(year, month, monthrange(year, month)[1])
    offset = (last_day.weekday() - 4) % 7
    return last_day - timedelta(days=offset)


def _next_trading_day(d: date) -> date:
    """Return the first weekday on or after ``d`` (no holiday calendar)."""
    cur = d
    while cur.weekday() >= 5:  # Sat=5, Sun=6
        cur = cur + timedelta(days=1)
    return cur


def derive_hold_meetings(
    rate_change_meetings: list[MeetingRow],
    start_year: int = 2008,
    end_year: int = 2026,
) -> list[MeetingRow]:
    """Generate the hold (no-change) meeting dates from the Junta cadence.

    Produces one MeetingRow per scheduled hold meeting in [start_year, end_year].
    The ``meeting_date`` is the *trading-day impact date* — the first weekday
    on or after the last Friday of the scheduled month — so it lines up with
    the convention used for rate-change meetings (effective-date / IBR-step
    date), keeping all rows in the calendar on a single time-axis convention.

    Hold meetings are de-duplicated against rate-change meetings by calendar
    week: if a rate-change meeting already covers a given ISO week, no hold
    row is generated for that week. This prevents double-counting in the
    per-week ``banrep_rate_surprise`` aggregation.

    Pure function.
    """
    def _week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())

    rate_change_weeks = {_week_start(m.meeting_date) for m in rate_change_meetings}
    hold_rows: list[MeetingRow] = []

    for y in range(start_year, end_year + 1):
        if y in _MONTHLY_MEETING_YEARS:
            months = range(1, 13)
        else:
            months = _EIGHT_PER_YEAR_MEETING_MONTHS
        for m in months:
            try:
                decision_friday = _last_friday_of_month(y, m)
            except ValueError:
                continue
            impact_date = _next_trading_day(decision_friday)
            if _week_start(impact_date) in rate_change_weeks:
                continue  # rate-change wins — skip hold row for this week
            hold_rows.append(MeetingRow(
                year=impact_date.year,
                meeting_date=impact_date,
                meeting_type="policy_rate_hold_inferred",
            ))
    return hold_rows


# ── Intervention (cached JSON) ───────────────────────────────────────────────


def _parse_amount(s: str) -> float | None:
    """Parse intervention amount string. Empty/whitespace → None."""
    s = s.strip()
    if not s:
        return None
    return float(s.replace(",", ""))


def load_intervention_from_json(json_path: str) -> list[InterventionRow]:
    """Load FX intervention data from cached Playwright-extracted JSON.

    Expected format: {"headers": [...], "rows": ["date\\tcol1\\tcol2\\t..."]}
    """
    with open(json_path) as f:
        data = _json.load(f)

    result: list[InterventionRow] = []
    for row_str in data["rows"]:
        parts = row_str.split("\t")
        date_str = parts[0]  # YYYY/MM/DD
        parsed_date = datetime.strptime(date_str, "%Y/%m/%d").date()

        amounts = [_parse_amount(parts[i + 1]) if i + 1 < len(parts) else None for i in range(8)]
        result.append(InterventionRow(
            date=parsed_date,
            discretionary=amounts[0],
            direct_purchase=amounts[1],
            put_volatility=amounts[2],
            call_volatility=amounts[3],
            put_reserve_accum=amounts[4],
            call_reserve_decum=amounts[5],
            ndf=amounts[6],
            fx_swaps=amounts[7],
        ))
    return result
