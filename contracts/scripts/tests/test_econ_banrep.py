"""Tests for BanRep data fetchers (TRM, IBR, intervention)."""
from __future__ import annotations

import pathlib
from datetime import date
from typing import Final

import duckdb
import pytest

from scripts.econ_schema import init_db
from scripts.econ_banrep import (
    parse_trm_socrata_response,
    load_intervention_from_json,
    parse_ibr_sdmx_xml,
    TrmRow,
    InterventionRow,
    IbrRow,
)

# ── Sample Socrata TRM response (real structure from datos.gov.co) ──

SAMPLE_TRM_RESPONSE: Final[list[dict[str, str]]] = [
    {"valor": "3603.19", "vigenciadesde": "2026-04-16T00:00:00.000", "vigenciahasta": "2026-04-16T00:00:00.000", "unidad": "COP"},
    {"valor": "3598.45", "vigenciadesde": "2026-04-15T00:00:00.000", "vigenciahasta": "2026-04-15T00:00:00.000", "unidad": "COP"},
    {"valor": "3610.00", "vigenciadesde": "2026-04-14T00:00:00.000", "vigenciahasta": "2026-04-14T00:00:00.000", "unidad": "COP"},
]


def test_parse_trm_socrata_response() -> None:
    """parse_trm_socrata_response extracts date + trm from Socrata JSON."""
    rows = parse_trm_socrata_response(SAMPLE_TRM_RESPONSE)
    assert len(rows) == 3
    assert rows[0] == TrmRow(date=date(2026, 4, 16), trm=3603.19)
    assert rows[1] == TrmRow(date=date(2026, 4, 15), trm=3598.45)


def test_parse_trm_empty_response() -> None:
    """Empty Socrata response returns empty list."""
    rows = parse_trm_socrata_response([])
    assert rows == []


def test_trm_rows_insert_into_db() -> None:
    """Parsed TRM rows can be inserted into banrep_trm_daily."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_trm_socrata_response(SAMPLE_TRM_RESPONSE)
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO banrep_trm_daily (date, trm) VALUES (?, ?)",
            [r.date, r.trm],
        )
    count = conn.execute("SELECT COUNT(*) FROM banrep_trm_daily").fetchone()
    assert count is not None and count[0] == 3


# ── IBR SDMX XML ──

SAMPLE_IBR_SDMX_XML: Final[str] = """<?xml version="1.0" encoding="UTF-8"?>
<mes:GenericData xmlns:mes="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
                 xmlns:gen="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
  <mes:DataSet>
    <gen:Series>
      <gen:SeriesKey>
        <gen:Value id="SUBJECT" value="IRIBRM00"/>
        <gen:Value id="UNIT_MEASURE" value="ER"/>
      </gen:SeriesKey>
      <gen:Obs>
        <gen:ObsDimension value="20260416"/>
        <gen:ObsValue value="11.249"/>
      </gen:Obs>
      <gen:Obs>
        <gen:ObsDimension value="20260415"/>
        <gen:ObsValue value="11.250"/>
      </gen:Obs>
    </gen:Series>
    <gen:Series>
      <gen:SeriesKey>
        <gen:Value id="SUBJECT" value="IRIBRM01"/>
        <gen:Value id="UNIT_MEASURE" value="ER"/>
      </gen:SeriesKey>
      <gen:Obs>
        <gen:ObsDimension value="20260416"/>
        <gen:ObsValue value="11.300"/>
      </gen:Obs>
    </gen:Series>
  </mes:DataSet>
</mes:GenericData>"""


def test_parse_ibr_sdmx_xml_extracts_overnight() -> None:
    """parse_ibr_sdmx_xml filters for IRIBRM00 + ER only."""
    rows = parse_ibr_sdmx_xml(SAMPLE_IBR_SDMX_XML)
    assert len(rows) == 2  # only overnight ER, not IRIBRM01
    assert rows[0] == IbrRow(date=date(2026, 4, 16), ibr_overnight_er=11.249)
    assert rows[1] == IbrRow(date=date(2026, 4, 15), ibr_overnight_er=11.250)


def test_parse_ibr_sdmx_xml_empty() -> None:
    """Empty SDMX XML returns empty list."""
    xml = '<?xml version="1.0"?><mes:GenericData xmlns:mes="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"><mes:DataSet/></mes:GenericData>'
    rows = parse_ibr_sdmx_xml(xml)
    assert rows == []


def test_ibr_rows_insert_into_db() -> None:
    """Parsed IBR rows insert into banrep_ibr_daily."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_ibr_sdmx_xml(SAMPLE_IBR_SDMX_XML)
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO banrep_ibr_daily (date, ibr_overnight_er) VALUES (?, ?)",
            [r.date, r.ibr_overnight_er],
        )
    count = conn.execute("SELECT COUNT(*) FROM banrep_ibr_daily").fetchone()
    assert count is not None and count[0] == 2


# ── Intervention JSON ──

INTERVENTION_JSON_PATH: Final[str] = str(
    pathlib.Path(__file__).resolve().parents[2] / "data" / "raw" / "banrep_fx_intervention.json"
)


def test_load_intervention_from_json() -> None:
    """load_intervention_from_json parses the real cached intervention file."""
    rows = load_intervention_from_json(INTERVENTION_JSON_PATH)
    assert len(rows) == 1674
    assert rows[0].date == date(1999, 12, 1)
    assert rows[-1].date == date(2024, 10, 4)


def test_intervention_first_row_has_put_reserve() -> None:
    """First intervention record (1999-12-01) has put_reserve_accum = 119.3."""
    rows = load_intervention_from_json(INTERVENTION_JSON_PATH)
    assert rows[0].put_reserve_accum == 119.3
    assert rows[0].discretionary is None
    assert rows[0].direct_purchase is None


def test_intervention_rows_insert_into_db() -> None:
    """Parsed intervention rows can be inserted into banrep_intervention_daily."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = load_intervention_from_json(INTERVENTION_JSON_PATH)
    for r in rows[:5]:
        conn.execute(
            "INSERT OR REPLACE INTO banrep_intervention_daily "
            "(date, discretionary, direct_purchase, put_volatility, call_volatility, "
            "put_reserve_accum, call_reserve_decum, ndf, fx_swaps) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [r.date, r.discretionary, r.direct_purchase, r.put_volatility,
             r.call_volatility, r.put_reserve_accum, r.call_reserve_decum,
             r.ndf, r.fx_swaps],
        )
    count = conn.execute("SELECT COUNT(*) FROM banrep_intervention_daily").fetchone()
    assert count is not None and count[0] == 5
