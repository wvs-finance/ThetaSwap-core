"""BanRep data fetchers: TRM (Socrata), IBR (SDMX), intervention (cached JSON).

Pure functions — no side effects except HTTP when explicitly called.
"""
from __future__ import annotations

import json as _json
from dataclasses import dataclass
from datetime import date, datetime
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
