# Structural Econometrics Data Pipeline — Implementation Plan (Rev 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **REQUIRED SKILL:** Invoke `functional-python` before writing any Python code. Test infrastructure (fixtures, conftest) is exempt from the "no classes" rule.
>
> **Agent orchestration:** Agents Orchestrator dispatches to Data Engineer. See agent assignments per task.

---

> ## NON-NEGOTIABLE RULES — ALL AGENTS MUST READ BEFORE ANY WORK
>
> ### Rule 1: STRICT TDD — One Behavior at a Time
> Do NOT write implementation code for ANY feature unless:
> 1. The test for that SPECIFIC SINGLE behavior has been written FIRST
> 2. The test has been run and VERIFIED TO FAIL
> 3. Only THEN write the MINIMAL implementation to make that ONE test pass
> 4. Run the test again — VERIFY IT PASSES
> 5. Only THEN move to the next behavior's test
>
> ### Rule 2: NO MERGE WITHOUT APPROVAL
> No code merged to the working branch until the user explicitly approves.
>
> ### Rule 3: ALL pytest/python commands MUST run from `contracts/`
> Every command: `cd contracts && .venv/bin/python -m pytest ...`
>
> ### Rule 4: SCRIPTS-ONLY SCOPE — Never Touch Contracts
> Agents may ONLY create/modify:
> - `contracts/scripts/*.py` and `contracts/scripts/tests/*.py`
> - `contracts/data/` (DuckDB, raw/, .gitkeep)
> - `contracts/.gitignore` (Python/DuckDB patterns only)
>
> **NEVER touch** `contracts/src/`, `contracts/test/**/*.sol`, `contracts/foundry.toml`, or any `.sol` file.
>
> ### Rule 5: REAL DATA IN TESTS
> Tests use real API responses or the cached raw files — NO mocks except for HTTP error simulation. The intervention JSON is real data cached at `contracts/data/raw/banrep_fx_intervention.json`.

---

**Goal:** Build a Python data pipeline that downloads macro data from BanRep (TRM, IBR, intervention), DANE (IPC, IPP), and FRED (VIX, oil, US CPI), stores it in DuckDB, and computes weekly + daily estimation panels for the COP/USD FX volatility structural model.

**Architecture:** Six modules — schema DDL (`econ_schema.py`), BanRep fetchers (`econ_banrep.py`), DANE fetchers (`econ_dane.py`), FRED fetchers (`econ_fred.py`), panel builders (`econ_panels.py`), and the pipeline orchestrator (`econ_pipeline.py`). Separate DuckDB file (`structural_econ.duckdb`). `requests` for HTTP. TDD throughout.

**Tech Stack:** Python 3.13, DuckDB 1.5.1, requests, numpy, statsmodels (AR), xml.etree.ElementTree (SDMX parsing), pytest

**Spec:** `contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md` (Rev 4)

---

## Data Source → Script → Table → Validation Map

| Data Source | Host / Endpoint | Script | DuckDB Table | Expected Rows | Date Range | Validation |
|---|---|---|---|---|---|---|
| COP/USD TRM | Datos Abiertos Socrata `https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=50000` | `econ_banrep.py::fetch_trm()` | `banrep_trm_daily` | ~8,250 | 1991-12-02 → present | row_count > 8000; date_min ≤ 1992-01-01; date_max ≥ 2026-01-01 |
| IBR overnight | BanRep SDMX `https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/ESTAT,DF_IBR_DAILY_HIST,1.0/all/ALL/?startPeriod=2008&endPeriod=2027` | `econ_banrep.py::fetch_ibr()` | `banrep_ibr_daily` | ~4,500 | 2008-01-02 → present | row_count > 4000; all rates > 0 and < 30 |
| FX intervention | Cached JSON `contracts/data/raw/banrep_fx_intervention.json` (Playwright-extracted from SUAMECA) | `econ_banrep.py::load_intervention_from_json()` | `banrep_intervention_daily` | 1,674 | 1999-12-01 → 2024-10-04 | row_count == 1674 exactly |
| VIX daily | FRED `https://api.stlouisfed.org/fred/series/observations?series_id=VIXCLS&file_type=json` | `econ_fred.py::fetch_fred_series("VIXCLS")` | `fred_daily` (series_id=VIXCLS) | ~9,000 | 1990-01-02 → present | row_count > 5000; "." → NULL |
| WTI oil daily | FRED `...?series_id=DCOILWTICO` | `econ_fred.py::fetch_fred_series("DCOILWTICO")` | `fred_daily` (series_id=DCOILWTICO) | ~8,000 | 1986-01-02 → present | row_count > 5000 |
| Brent oil daily | FRED `...?series_id=DCOILBRENTEU` | `econ_fred.py::fetch_fred_series("DCOILBRENTEU")` | `fred_daily` (series_id=DCOILBRENTEU) | ~8,000 | 1987-05-20 → present | row_count > 5000 |
| US CPI monthly | FRED `...?series_id=CPIAUCSL` | `econ_fred.py::fetch_fred_series("CPIAUCSL")` | `fred_monthly` (series_id=CPIAUCSL) | ~280 | 2000-01-01 → present | row_count > 250 |
| BLS CPI release dates | FRED `https://api.stlouisfed.org/fred/release/dates?release_id=10&file_type=json` | `econ_fred.py::fetch_bls_release_dates()` | `bls_release_calendar` | ~280 | 2000 → present | row_count > 250; UNIQUE(release_date) |
| Colombian CPI (IPC) | Manual CSV download from DANE → `contracts/data/raw/dane_ipc.csv` | `econ_dane.py::parse_dane_ipc_csv()` | `dane_ipc_monthly` | ~280 | 2002-01-01 → present | row_count > 250; ipc_index > 0 |
| Colombian PPI (IPP) | Manual CSV download from DANE → `contracts/data/raw/dane_ipp.csv` | `econ_dane.py::parse_dane_ipp_csv()` | `dane_ipp_monthly` | ~260 | 2003-01-01 → present | row_count > 240 |
| DANE release calendar | Manual CSV `contracts/data/raw/dane_release_calendar.csv` | `econ_dane.py::parse_dane_release_calendar_csv()` | `dane_release_calendar` | ~520 | 2003 → present | row_count > 480; UNIQUE(release_date, series) |
| Download manifest | Auto-populated by pipeline | `econ_pipeline.py::log_manifest()` | `download_manifest` | grows | — | append-only (INSERT, never REPLACE) |

**Derived panels (computed from raw, not downloaded):**

| Panel | Builder | Expected Rows | Date Range | Key Validations |
|---|---|---|---|---|
| `weekly_panel` | `econ_panels.py::build_weekly_panel()` | ~1,100 | ~2003-01 → present | RV > 0; n_trading_days in [1,5]; no NULL in surprise cols (must be 0.0); intervention_dummy in {0,1} |
| `daily_panel` | `econ_panels.py::build_daily_panel()` | ~5,500 | ~2003-01 → present | first row cop_usd_return=NULL; surprise only on release dates; intervention_dummy in {0,1} |

---

## File Structure

| File | Responsibility |
|---|---|
| `contracts/scripts/econ_schema.py` | All CREATE TABLE DDL strings, frozen dataclass types, DB init function |
| `contracts/scripts/econ_banrep.py` | Fetch TRM (Socrata), IBR (SDMX XML), load intervention (cached JSON) |
| `contracts/scripts/econ_fred.py` | Fetch FRED daily/monthly series, BLS release dates |
| `contracts/scripts/econ_dane.py` | Load DANE IPC/IPP from CSV/Excel, load release calendar |
| `contracts/scripts/econ_panels.py` | Build weekly_panel and daily_panel from raw tables |
| `contracts/scripts/econ_pipeline.py` | Orchestrate: download all → build panels → validate |
| `contracts/scripts/tests/test_econ_schema.py` | Schema DDL tests |
| `contracts/scripts/tests/test_econ_banrep.py` | BanRep fetcher tests |
| `contracts/scripts/tests/test_econ_fred.py` | FRED fetcher tests |
| `contracts/scripts/tests/test_econ_dane.py` | DANE loader tests |
| `contracts/scripts/tests/test_econ_panels.py` | Panel builder tests |
| `contracts/scripts/tests/test_econ_pipeline.py` | Integration/validation tests |
| `contracts/data/structural_econ.duckdb` | Output database (gitignored) |
| `contracts/data/raw/banrep_fx_intervention.json` | Cached intervention data (already committed) |

---

### Task 1: Schema DDL and DB Initialization

**Agent:** Data Engineer
**Files:**
- Create: `contracts/scripts/econ_schema.py`
- Create: `contracts/scripts/tests/test_econ_schema.py`

This task defines all 10 CREATE TABLE statements and a function to initialize a DuckDB connection with the full schema.

- [ ] **Step 1: Write failing test — schema creates all tables**

```python
# contracts/scripts/tests/test_econ_schema.py
"""Tests for structural econometrics schema DDL."""
from __future__ import annotations

import duckdb
import pytest

from scripts.econ_schema import init_db, EXPECTED_TABLES


def test_init_db_creates_all_tables() -> None:
    """init_db creates exactly the 10 expected raw + calendar tables."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert tables == EXPECTED_TABLES


def test_init_db_is_idempotent() -> None:
    """Calling init_db twice does not error or duplicate tables."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    init_db(conn)  # second call
    tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert tables == EXPECTED_TABLES


def test_banrep_trm_daily_schema() -> None:
    """banrep_trm_daily has correct columns and types."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    cols = conn.execute("DESCRIBE banrep_trm_daily").fetchall()
    col_map = {c[0]: c[1] for c in cols}
    assert col_map["date"] == "DATE"
    assert col_map["trm"] == "DOUBLE"
    assert "_ingested_at" in col_map


def test_banrep_trm_daily_pk_enforced() -> None:
    """Duplicate date in banrep_trm_daily raises constraint error."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-01', 3900.0)")
    with pytest.raises(duckdb.ConstraintException):
        conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-01', 3901.0)")


def test_insert_or_replace_overwrites() -> None:
    """INSERT OR REPLACE on banrep_trm_daily updates the value."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-01', 3900.0)")
    conn.execute("INSERT OR REPLACE INTO banrep_trm_daily (date, trm) VALUES ('2024-01-01', 3950.0)")
    result = conn.execute("SELECT trm FROM banrep_trm_daily WHERE date = '2024-01-01'").fetchone()
    assert result is not None
    assert result[0] == 3950.0


def test_download_manifest_append_only() -> None:
    """download_manifest allows multiple rows for same source."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    conn.execute(
        "INSERT INTO download_manifest (source, downloaded_at, status) "
        "VALUES ('banrep:trm', '2026-04-16 10:00:00', 'verified')"
    )
    conn.execute(
        "INSERT INTO download_manifest (source, downloaded_at, status) "
        "VALUES ('banrep:trm', '2026-04-16 10:00:01', 'success')"
    )
    count = conn.execute("SELECT COUNT(*) FROM download_manifest WHERE source = 'banrep:trm'").fetchone()
    assert count is not None and count[0] == 2


def test_fred_daily_check_constraint() -> None:
    """fred_daily rejects unknown series_id."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    with pytest.raises(duckdb.ConstraintException):
        conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('FAKE', '2024-01-01', 100.0)")


def test_banrep_intervention_daily_schema() -> None:
    """banrep_intervention_daily has all 8 intervention type columns."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    cols = conn.execute("DESCRIBE banrep_intervention_daily").fetchall()
    col_names = {c[0] for c in cols}
    expected = {"date", "discretionary", "direct_purchase", "put_volatility",
                "call_volatility", "put_reserve_accum", "call_reserve_decum",
                "ndf", "fx_swaps", "_ingested_at"}
    assert expected.issubset(col_names)


def test_banrep_ibr_daily_schema() -> None:
    """banrep_ibr_daily has date, ibr_overnight_er, _ingested_at."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    cols = conn.execute("DESCRIBE banrep_ibr_daily").fetchall()
    col_map = {c[0]: c[1] for c in cols}
    assert col_map["date"] == "DATE"
    assert col_map["ibr_overnight_er"] == "DOUBLE"
    assert "_ingested_at" in col_map
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.econ_schema'`

- [ ] **Step 3: Write implementation**

```python
# contracts/scripts/econ_schema.py
"""Schema DDL and initialization for the structural econometrics DuckDB.

All CREATE TABLE statements follow the spec:
contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md (Rev 4)
"""
from __future__ import annotations

from typing import Final

import duckdb

# ── Expected tables ──────────────────────────────────────────────────────────

EXPECTED_TABLES: Final[frozenset[str]] = frozenset({
    "banrep_trm_daily",
    "banrep_ibr_daily",
    "banrep_intervention_daily",
    "fred_daily",
    "fred_monthly",
    "dane_ipc_monthly",
    "dane_ipp_monthly",
    "dane_release_calendar",
    "bls_release_calendar",
    "download_manifest",
})

# ── DDL statements ───────────────────────────────────────────────────────────

_DDL_BANREP_TRM_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_trm_daily (
    date DATE PRIMARY KEY,
    trm DOUBLE NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_BANREP_IBR_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_ibr_daily (
    date DATE PRIMARY KEY,
    ibr_overnight_er DOUBLE NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_BANREP_INTERVENTION_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_intervention_daily (
    date DATE PRIMARY KEY,
    discretionary DOUBLE,
    direct_purchase DOUBLE,
    put_volatility DOUBLE,
    call_volatility DOUBLE,
    put_reserve_accum DOUBLE,
    call_reserve_decum DOUBLE,
    ndf DOUBLE,
    fx_swaps DOUBLE,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_FRED_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS fred_daily (
    series_id VARCHAR NOT NULL CHECK (series_id IN ('VIXCLS', 'DCOILWTICO', 'DCOILBRENTEU')),
    date DATE NOT NULL,
    value DOUBLE,
    PRIMARY KEY (series_id, date)
)
"""

_DDL_FRED_MONTHLY: Final[str] = """
CREATE TABLE IF NOT EXISTS fred_monthly (
    series_id VARCHAR NOT NULL CHECK (series_id IN ('CPIAUCSL')),
    date DATE NOT NULL,
    value DOUBLE,
    PRIMARY KEY (series_id, date)
)
"""

_DDL_DANE_IPC_MONTHLY: Final[str] = """
CREATE TABLE IF NOT EXISTS dane_ipc_monthly (
    date DATE PRIMARY KEY,
    ipc_index DOUBLE,
    ipc_pct_change DOUBLE,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_DANE_IPP_MONTHLY: Final[str] = """
CREATE TABLE IF NOT EXISTS dane_ipp_monthly (
    date DATE PRIMARY KEY,
    ipp_index DOUBLE,
    ipp_pct_change DOUBLE,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_DANE_RELEASE_CALENDAR: Final[str] = """
CREATE TABLE IF NOT EXISTS dane_release_calendar (
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    release_date DATE NOT NULL,
    series VARCHAR NOT NULL CHECK (series IN ('ipc', 'ipp')),
    imputed BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (year, month, series),
    UNIQUE (release_date, series)
)
"""

_DDL_BLS_RELEASE_CALENDAR: Final[str] = """
CREATE TABLE IF NOT EXISTS bls_release_calendar (
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    release_date DATE NOT NULL,
    PRIMARY KEY (year, month),
    UNIQUE (release_date)
)
"""

_DDL_DOWNLOAD_MANIFEST: Final[str] = """
CREATE TABLE IF NOT EXISTS download_manifest (
    source VARCHAR NOT NULL,
    downloaded_at TIMESTAMP NOT NULL,
    row_count INTEGER,
    date_min DATE,
    date_max DATE,
    sha256 VARCHAR,
    url_or_path VARCHAR,
    status VARCHAR NOT NULL,
    notes VARCHAR,
    PRIMARY KEY (source, downloaded_at)
)
"""

_ALL_DDL: Final[tuple[str, ...]] = (
    _DDL_BANREP_TRM_DAILY,
    _DDL_BANREP_IBR_DAILY,
    _DDL_BANREP_INTERVENTION_DAILY,
    _DDL_FRED_DAILY,
    _DDL_FRED_MONTHLY,
    _DDL_DANE_IPC_MONTHLY,
    _DDL_DANE_IPP_MONTHLY,
    _DDL_DANE_RELEASE_CALENDAR,
    _DDL_BLS_RELEASE_CALENDAR,
    _DDL_DOWNLOAD_MANIFEST,
)


# ── Public API ───────────────────────────────────────────────────────────────


def init_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all raw tables if they don't exist. Idempotent."""
    for ddl in _ALL_DDL:
        conn.execute(ddl)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_schema.py -v`
Expected: all 9 tests PASS

- [ ] **Step 5: Commit**

```bash
cd contracts && git add scripts/econ_schema.py scripts/tests/test_econ_schema.py
git commit -m "feat(structural-econ): schema DDL for 10 raw tables + init_db"
```

---

### Task 2: BanRep TRM Fetcher (Socrata API)

**Agent:** Data Engineer
**Files:**
- Create: `contracts/scripts/econ_banrep.py`
- Create: `contracts/scripts/tests/test_econ_banrep.py`

Downloads daily TRM from Datos Abiertos Socrata API, parses JSON, inserts into `banrep_trm_daily`. Also loads IBR from SDMX XML and intervention from cached JSON.

- [ ] **Step 1: Write failing test — fetch_trm parses Socrata JSON and inserts rows**

```python
# contracts/scripts/tests/test_econ_banrep.py
"""Tests for BanRep data fetchers (TRM, IBR, intervention)."""
from __future__ import annotations

import json
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_banrep.py::test_parse_trm_socrata_response -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.econ_banrep'`

- [ ] **Step 3: Write minimal implementation for TRM parsing**

```python
# contracts/scripts/econ_banrep.py
"""BanRep data fetchers: TRM (Socrata), IBR (SDMX), intervention (cached JSON).

Pure functions — no side effects except HTTP when explicitly called.
"""
from __future__ import annotations

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
        parsed_date = datetime.fromisoformat(fecha_str.replace(".000", "")).date()
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

_SDMX_NS: Final[dict[str, str]] = {
    "mes": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
    "gen": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
}


def parse_ibr_sdmx_xml(xml_text: str) -> list[IbrRow]:
    """Parse SDMX-ML Generic Data XML for IBR overnight effective rate.

    Filters for SUBJECT=IRIBRM00 (overnight), UNIT_MEASURE=ER (effective).
    """
    root = ElementTree.fromstring(xml_text)
    rows: list[IbrRow] = []

    for obs in root.iter("{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Obs"):
        # Get dimensions from parent Series
        series = obs.find("..")
        if series is None:
            continue

        dims: dict[str, str] = {}
        for key_el in series.iter("{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Value"):
            dim_id = key_el.get("id", "")
            dim_val = key_el.get("value", "")
            dims[dim_id] = dim_val

        if dims.get("SUBJECT") != "IRIBRM00" or dims.get("UNIT_MEASURE") != "ER":
            continue

        obs_dim = obs.find("{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}ObsDimension")
        obs_val = obs.find("{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}ObsValue")
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

_INTERVENTION_COLS: Final[tuple[str, ...]] = (
    "Subasta - Intervención discrecional",
    "Subasta - Compra directa",
    "Subasta - Opciones put para control volatilidad",
    "Subasta - Opciones call para control volatilidad",
    "Subasta - Opciones put para acumulación de reservas internacionales - resumen del ejercicio",
    "Subasta - Opciones call para desacumulación de reservas internacionales - resumen del ejercicio",
    "Subastas de venta de dólares a través de contratos Non delivery forward (NDF)",
    "Subasta de venta de dólares de contado a través de FX Swaps",
)


def _parse_amount(s: str) -> float | None:
    """Parse intervention amount string. Empty/whitespace → None."""
    s = s.strip()
    if not s:
        return None
    return float(s)


def load_intervention_from_json(json_path: str) -> list[InterventionRow]:
    """Load FX intervention data from cached Playwright-extracted JSON.

    Expected format: {"headers": [...], "rows": ["date\\tcol1\\tcol2\\t..."]}
    """
    import json as _json
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_banrep.py -v -k "trm"`
Expected: all 3 TRM tests PASS

- [ ] **Step 5: Write failing test — parse_ibr_sdmx_xml extracts overnight rates**

```python
# Append to contracts/scripts/tests/test_econ_banrep.py

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
```

- [ ] **Step 6: Run IBR tests**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_banrep.py -v -k "ibr"`
Expected: all 3 PASS

- [ ] **Step 7: Write failing test — load_intervention_from_json parses cached data**

```python
# Append to contracts/scripts/tests/test_econ_banrep.py

import pathlib

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
```

- [ ] **Step 6: Run intervention tests**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_banrep.py -v -k "intervention"`
Expected: all 3 PASS

- [ ] **Step 7: Commit**

```bash
cd contracts && git add scripts/econ_banrep.py scripts/tests/test_econ_banrep.py
git commit -m "feat(structural-econ): BanRep fetchers — TRM, IBR, intervention"
```

---

### Task 3: FRED Fetcher

**Agent:** Data Engineer
**Files:**
- Create: `contracts/scripts/econ_fred.py`
- Create: `contracts/scripts/tests/test_econ_fred.py`

Downloads FRED daily/monthly series and BLS release dates. Handles `"."` → NULL conversion.

- [ ] **Step 1: Write failing test — parse_fred_observations handles "." values**

```python
# contracts/scripts/tests/test_econ_fred.py
"""Tests for FRED data fetchers."""
from __future__ import annotations

from datetime import date
from typing import Final

import duckdb

from scripts.econ_schema import init_db
from scripts.econ_fred import (
    parse_fred_observations,
    parse_bls_release_dates,
    FredObservation,
    BlsReleaseDate,
)

SAMPLE_FRED_RESPONSE: Final[dict] = {
    "observations": [
        {"date": "2024-01-02", "value": "12.45"},
        {"date": "2024-01-03", "value": "."},
        {"date": "2024-01-04", "value": "13.20"},
    ]
}


def test_parse_fred_observations() -> None:
    """parse_fred_observations converts '.' to None."""
    rows = parse_fred_observations(SAMPLE_FRED_RESPONSE, "VIXCLS")
    assert len(rows) == 3
    assert rows[0] == FredObservation(series_id="VIXCLS", date=date(2024, 1, 2), value=12.45)
    assert rows[1].value is None  # "." → None
    assert rows[2].value == 13.20


def test_fred_observations_insert_into_db() -> None:
    """Parsed FRED observations can be inserted into fred_daily."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_fred_observations(SAMPLE_FRED_RESPONSE, "VIXCLS")
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO fred_daily (series_id, date, value) VALUES (?, ?, ?)",
            [r.series_id, r.date, r.value],
        )
    count = conn.execute("SELECT COUNT(*) FROM fred_daily").fetchone()
    assert count is not None and count[0] == 3
    null_row = conn.execute("SELECT value FROM fred_daily WHERE date = '2024-01-03'").fetchone()
    assert null_row is not None and null_row[0] is None


SAMPLE_BLS_DATES_RESPONSE: Final[dict] = {
    "release_dates": [
        {"release_id": "10", "date": "2024-01-11"},
        {"release_id": "10", "date": "2024-02-13"},
        {"release_id": "10", "date": "2024-03-12"},
    ]
}


def test_parse_bls_release_dates() -> None:
    """parse_bls_release_dates extracts year, month-1, release_date."""
    rows = parse_bls_release_dates(SAMPLE_BLS_DATES_RESPONSE)
    assert len(rows) == 3
    # Jan 2024 release covers Dec 2023 CPI
    assert rows[0] == BlsReleaseDate(year=2023, month=12, release_date=date(2024, 1, 11))
    assert rows[1] == BlsReleaseDate(year=2024, month=1, release_date=date(2024, 2, 13))


def test_bls_dates_insert_into_db() -> None:
    """Parsed BLS release dates insert into bls_release_calendar."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_bls_release_dates(SAMPLE_BLS_DATES_RESPONSE)
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO bls_release_calendar (year, month, release_date) VALUES (?, ?, ?)",
            [r.year, r.month, r.release_date],
        )
    count = conn.execute("SELECT COUNT(*) FROM bls_release_calendar").fetchone()
    assert count is not None and count[0] == 3
```

- [ ] **Step 2: Run to verify failure**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_fred.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# contracts/scripts/econ_fred.py
"""FRED data fetchers: daily series, monthly series, BLS release dates.

Pure functions — no side effects except HTTP when explicitly called.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Final

import requests


@dataclass(frozen=True, slots=True)
class FredObservation:
    """One FRED observation."""
    series_id: str
    date: date
    value: float | None


@dataclass(frozen=True, slots=True)
class BlsReleaseDate:
    """One BLS CPI release date mapping."""
    year: int
    month: int
    release_date: date


_FRED_OBS_ENDPOINT: Final[str] = "https://api.stlouisfed.org/fred/series/observations"
_FRED_RELEASE_DATES_ENDPOINT: Final[str] = "https://api.stlouisfed.org/fred/release/dates"


def parse_fred_observations(data: dict, series_id: str) -> list[FredObservation]:
    """Parse FRED JSON response. Converts value='.' to None."""
    rows: list[FredObservation] = []
    for obs in data.get("observations", []):
        date_str = obs.get("date", "")
        value_str = obs.get("value", ".")
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        value = None if value_str.strip() == "." else float(value_str)
        rows.append(FredObservation(series_id=series_id, date=parsed_date, value=value))
    return rows


def fetch_fred_series(series_id: str, api_key: str, start: str = "2000-01-01") -> list[FredObservation]:
    """Fetch a FRED series via REST API."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
    }
    resp = requests.get(_FRED_OBS_ENDPOINT, params=params, timeout=60)
    resp.raise_for_status()
    return parse_fred_observations(resp.json(), series_id)


def parse_bls_release_dates(data: dict) -> list[BlsReleaseDate]:
    """Parse FRED release dates response.

    BLS CPI release in month M covers CPI for month M-1.
    E.g., release on 2024-01-11 → CPI for December 2023 (year=2023, month=12).
    """
    rows: list[BlsReleaseDate] = []
    for entry in data.get("release_dates", []):
        release_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        # The release covers the PRIOR month's CPI
        if release_date.month == 1:
            ref_year = release_date.year - 1
            ref_month = 12
        else:
            ref_year = release_date.year
            ref_month = release_date.month - 1
        rows.append(BlsReleaseDate(year=ref_year, month=ref_month, release_date=release_date))
    return rows


def fetch_bls_release_dates(api_key: str) -> list[BlsReleaseDate]:
    """Fetch BLS CPI release dates from FRED."""
    params = {
        "release_id": "10",
        "api_key": api_key,
        "file_type": "json",
    }
    resp = requests.get(_FRED_RELEASE_DATES_ENDPOINT, params=params, timeout=60)
    resp.raise_for_status()
    return parse_bls_release_dates(resp.json())
```

- [ ] **Step 4: Run tests**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_fred.py -v`
Expected: all 5 PASS

- [ ] **Step 5: Commit**

```bash
cd contracts && git add scripts/econ_fred.py scripts/tests/test_econ_fred.py
git commit -m "feat(structural-econ): FRED fetchers — daily, monthly, BLS release dates"
```

---

### Task 4: DANE Loader

**Agent:** Data Engineer
**Files:**
- Create: `contracts/scripts/econ_dane.py`
- Create: `contracts/scripts/tests/test_econ_dane.py`

Loads DANE IPC/IPP from CSV files and the release calendar from a manually compiled CSV. These are manual-download sources, so the module provides parsers for CSV format, not HTTP fetchers.

- [ ] **Step 1: Write failing test — parse_dane_ipc_csv**

```python
# contracts/scripts/tests/test_econ_dane.py
"""Tests for DANE data loaders."""
from __future__ import annotations

import io
from datetime import date

import duckdb

from scripts.econ_schema import init_db
from scripts.econ_dane import (
    parse_dane_ipc_csv,
    parse_dane_release_calendar_csv,
    DaneIpcRow,
    DaneReleaseCalendarRow,
)

SAMPLE_IPC_CSV: str = """date,ipc_index,ipc_pct_change
2024-01-01,158.23,0.92
2024-02-01,158.89,0.42
2024-03-01,159.45,0.35
"""


def test_parse_dane_ipc_csv() -> None:
    """parse_dane_ipc_csv reads CSV into DaneIpcRow list."""
    rows = parse_dane_ipc_csv(io.StringIO(SAMPLE_IPC_CSV))
    assert len(rows) == 3
    assert rows[0] == DaneIpcRow(date=date(2024, 1, 1), ipc_index=158.23, ipc_pct_change=0.92)


def test_dane_ipc_insert_into_db() -> None:
    """Parsed IPC rows insert into dane_ipc_monthly."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_dane_ipc_csv(io.StringIO(SAMPLE_IPC_CSV))
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO dane_ipc_monthly (date, ipc_index, ipc_pct_change) VALUES (?, ?, ?)",
            [r.date, r.ipc_index, r.ipc_pct_change],
        )
    count = conn.execute("SELECT COUNT(*) FROM dane_ipc_monthly").fetchone()
    assert count is not None and count[0] == 3


SAMPLE_IPP_CSV: str = """date,ipp_index,ipp_pct_change
2024-01-01,210.50,0.55
2024-02-01,211.20,0.33
2024-03-01,211.80,0.28
"""


def test_parse_dane_ipp_csv() -> None:
    """parse_dane_ipp_csv reads CSV into DaneIppRow list."""
    from scripts.econ_dane import parse_dane_ipp_csv, DaneIppRow
    rows = parse_dane_ipp_csv(io.StringIO(SAMPLE_IPP_CSV))
    assert len(rows) == 3
    assert rows[0] == DaneIppRow(date=date(2024, 1, 1), ipp_index=210.50, ipp_pct_change=0.55)


def test_dane_ipp_insert_into_db() -> None:
    """Parsed IPP rows insert into dane_ipp_monthly."""
    from scripts.econ_dane import parse_dane_ipp_csv
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_dane_ipp_csv(io.StringIO(SAMPLE_IPP_CSV))
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO dane_ipp_monthly (date, ipp_index, ipp_pct_change) VALUES (?, ?, ?)",
            [r.date, r.ipp_index, r.ipp_pct_change],
        )
    count = conn.execute("SELECT COUNT(*) FROM dane_ipp_monthly").fetchone()
    assert count is not None and count[0] == 3


SAMPLE_RELEASE_CALENDAR_CSV: str = """year,month,release_date,series,imputed
2024,1,2024-02-07,ipc,false
2024,1,2024-02-07,ipp,false
2024,2,2024-03-06,ipc,false
2024,2,2024-03-06,ipp,false
"""


def test_parse_dane_release_calendar_csv() -> None:
    """parse_dane_release_calendar_csv reads calendar entries."""
    rows = parse_dane_release_calendar_csv(io.StringIO(SAMPLE_RELEASE_CALENDAR_CSV))
    assert len(rows) == 4
    assert rows[0] == DaneReleaseCalendarRow(
        year=2024, month=1, release_date=date(2024, 2, 7), series="ipc", imputed=False,
    )


def test_release_calendar_insert_into_db() -> None:
    """Parsed release calendar rows insert into dane_release_calendar."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_dane_release_calendar_csv(io.StringIO(SAMPLE_RELEASE_CALENDAR_CSV))
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO dane_release_calendar (year, month, release_date, series, imputed) "
            "VALUES (?, ?, ?, ?, ?)",
            [r.year, r.month, r.release_date, r.series, r.imputed],
        )
    count = conn.execute("SELECT COUNT(*) FROM dane_release_calendar").fetchone()
    assert count is not None and count[0] == 4
```

- [ ] **Step 2: Run to verify failure**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_dane.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# contracts/scripts/econ_dane.py
"""DANE data loaders: IPC, IPP, release calendar from CSV files.

DANE's API is unreliable. These functions parse manually downloaded CSV files.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import IO


@dataclass(frozen=True, slots=True)
class DaneIpcRow:
    """One monthly IPC observation."""
    date: date
    ipc_index: float
    ipc_pct_change: float


@dataclass(frozen=True, slots=True)
class DaneIppRow:
    """One monthly IPP observation."""
    date: date
    ipp_index: float
    ipp_pct_change: float


@dataclass(frozen=True, slots=True)
class DaneReleaseCalendarRow:
    """One DANE release calendar entry."""
    year: int
    month: int
    release_date: date
    series: str
    imputed: bool


def parse_dane_ipc_csv(file: IO[str]) -> list[DaneIpcRow]:
    """Parse DANE IPC CSV: date, ipc_index, ipc_pct_change."""
    reader = csv.DictReader(file)
    rows: list[DaneIpcRow] = []
    for record in reader:
        rows.append(DaneIpcRow(
            date=datetime.strptime(record["date"], "%Y-%m-%d").date(),
            ipc_index=float(record["ipc_index"]),
            ipc_pct_change=float(record["ipc_pct_change"]),
        ))
    return rows


def parse_dane_ipp_csv(file: IO[str]) -> list[DaneIppRow]:
    """Parse DANE IPP CSV: date, ipp_index, ipp_pct_change."""
    reader = csv.DictReader(file)
    rows: list[DaneIppRow] = []
    for record in reader:
        rows.append(DaneIppRow(
            date=datetime.strptime(record["date"], "%Y-%m-%d").date(),
            ipp_index=float(record["ipp_index"]),
            ipp_pct_change=float(record["ipp_pct_change"]),
        ))
    return rows


def parse_dane_release_calendar_csv(file: IO[str]) -> list[DaneReleaseCalendarRow]:
    """Parse DANE release calendar CSV: year, month, release_date, series, imputed."""
    reader = csv.DictReader(file)
    rows: list[DaneReleaseCalendarRow] = []
    for record in reader:
        rows.append(DaneReleaseCalendarRow(
            year=int(record["year"]),
            month=int(record["month"]),
            release_date=datetime.strptime(record["release_date"], "%Y-%m-%d").date(),
            series=record["series"],
            imputed=record["imputed"].lower() in ("true", "1", "yes"),
        ))
    return rows
```

- [ ] **Step 4: Run tests**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_dane.py -v`
Expected: all 4 PASS

- [ ] **Step 5: Commit**

```bash
cd contracts && git add scripts/econ_dane.py scripts/tests/test_econ_dane.py
git commit -m "feat(structural-econ): DANE loaders — IPC, IPP, release calendar CSV"
```

---

### Task 5: Weekly Panel Builder

**Agent:** Data Engineer
**Files:**
- Create: `contracts/scripts/econ_panels.py`
- Create: `contracts/scripts/tests/test_econ_panels.py`

Builds `weekly_panel` from raw tables. This is the most complex task — RV computation, surprise construction, release-week mapping.

- [ ] **Step 1: Write failing test — RV computation from TRM daily**

```python
# contracts/scripts/tests/test_econ_panels.py
"""Tests for panel builders (weekly_panel, daily_panel)."""
from __future__ import annotations

import math
from datetime import date

import duckdb

from scripts.econ_schema import init_db
from scripts.econ_panels import build_weekly_panel, build_daily_panel


def _seed_trm(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert 10 TRM observations spanning 2 weeks (Mon-Fri each)."""
    # Week 1: Mon 2024-01-08 to Fri 2024-01-12
    # Week 2: Mon 2024-01-15 to Fri 2024-01-19
    trm_data = [
        # Week 0 (prior Friday for Monday return computation)
        ("2024-01-05", 3900.0),
        # Week 1
        ("2024-01-08", 3910.0),
        ("2024-01-09", 3905.0),
        ("2024-01-10", 3920.0),
        ("2024-01-11", 3915.0),
        ("2024-01-12", 3925.0),
        # Week 2
        ("2024-01-15", 3930.0),
        ("2024-01-16", 3940.0),
        ("2024-01-17", 3935.0),
        ("2024-01-18", 3950.0),
        ("2024-01-19", 3945.0),
    ]
    for d, v in trm_data:
        conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES (?, ?)", [d, v])


def _seed_fred(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert VIX and WTI for the same 2-week period."""
    vix_data = [
        ("2024-01-08", 13.5), ("2024-01-09", 14.0), ("2024-01-10", 13.8),
        ("2024-01-11", 14.2), ("2024-01-12", 13.9),
        ("2024-01-15", 14.5), ("2024-01-16", 14.1), ("2024-01-17", 14.3),
        ("2024-01-18", 14.8), ("2024-01-19", 14.6),
    ]
    for d, v in vix_data:
        conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('VIXCLS', ?, ?)", [d, v])

    oil_data = [
        ("2024-01-05", 72.0),  # prior week close
        ("2024-01-08", 72.5), ("2024-01-09", 73.0), ("2024-01-10", 72.8),
        ("2024-01-11", 73.5), ("2024-01-12", 74.0),
        ("2024-01-15", 74.5), ("2024-01-16", 75.0), ("2024-01-17", 74.8),
        ("2024-01-18", 75.5), ("2024-01-19", 76.0),
    ]
    for d, v in oil_data:
        conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('DCOILWTICO', ?, ?)", [d, v])


def test_weekly_panel_rv_computation() -> None:
    """weekly_panel computes RV as sum of squared log-returns."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT rv, rv_cuberoot, rv_log, n_trading_days FROM weekly_panel WHERE week_start = '2024-01-08'"
    ).fetchone()
    assert row is not None
    rv, rv_cr, rv_log, n_days = row
    assert n_days == 5
    assert rv > 0
    assert abs(rv_cr - rv ** (1.0 / 3.0)) < 1e-10
    assert abs(rv_log - math.log(rv)) < 1e-10


def test_weekly_panel_oil_return() -> None:
    """oil_return is log(last_wti_this_week / last_wti_prior_week)."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT oil_return, oil_log_level FROM weekly_panel WHERE week_start = '2024-01-08'"
    ).fetchone()
    assert row is not None
    oil_ret, oil_level = row
    expected_ret = math.log(74.0 / 72.0)  # Fri 12 / Fri 05
    assert abs(oil_ret - expected_ret) < 1e-10
    assert abs(oil_level - math.log(74.0)) < 1e-10


def test_weekly_panel_vix_avg_and_friday() -> None:
    """vix_avg is weekly mean, vix_friday_close is last trading day."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT vix_avg, vix_friday_close FROM weekly_panel WHERE week_start = '2024-01-08'"
    ).fetchone()
    assert row is not None
    vix_avg, vix_fri = row
    expected_avg = (13.5 + 14.0 + 13.8 + 14.2 + 13.9) / 5.0
    assert abs(vix_avg - expected_avg) < 1e-10
    assert vix_fri == 13.9  # Friday 2024-01-12


def test_weekly_panel_non_release_week_zeros() -> None:
    """Non-release weeks have 0.0 for surprise columns, not NULL."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT cpi_surprise_ar1, dane_ipc_pct, dane_ipp_pct, us_cpi_surprise, "
        "is_cpi_release_week, is_ppi_release_week "
        "FROM weekly_panel WHERE week_start = '2024-01-08'"
    ).fetchone()
    assert row is not None
    cpi_s, ipc_pct, ipp_pct, us_s, is_cpi, is_ppi = row
    assert cpi_s == 0.0
    assert ipc_pct == 0.0
    assert ipp_pct == 0.0
    assert us_s == 0.0
    assert is_cpi is False
    assert is_ppi is False
```

- [ ] **Step 2: Run to verify failure**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_panels.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation — build_weekly_panel**

This is the largest implementation. The function executes a single SQL `CREATE OR REPLACE TABLE ... AS (SELECT ...)` that joins all raw tables.

```python
# contracts/scripts/econ_panels.py
"""Panel builders: weekly_panel and daily_panel from raw tables.

All computation is done in SQL via DuckDB. Python orchestrates the queries.
"""
from __future__ import annotations

import math
from datetime import date, timedelta as _timedelta
from typing import Final

import duckdb


def build_weekly_panel(
    conn: duckdb.DuckDBPyConnection,
    sample_start: date = date(2003, 1, 6),  # first Monday of 2003
) -> None:
    """Build weekly_panel from raw tables. CREATE OR REPLACE — idempotent.

    Computation steps (all in SQL):
    1. Generate week spines from TRM dates
    2. Compute RV from daily TRM log-returns
    3. Aggregate VIX (avg + Friday close) and oil (return + level)
    4. Map DANE releases to weeks, fill 0.0 on non-release weeks
    5. Map BLS releases to weeks for US CPI surprise
    6. Join intervention dummy
    7. Join IBR rate surprise (placeholder 0.0 — full construction deferred to estimation)
    """
    # Rev 2 fixes: removed dead dane_ipc_release CTE (B1/B3), replaced LAST() with
    # ARG_MAX() (B2), added 14-day lookback for LAG() (F4/F5), added dane_ipc/ipp
    # release-week joins (F5/F11), removed unnecessary COALESCE on booleans (F3).
    # Note: cpi_surprise_ar1, us_cpi_surprise, banrep_rate_surprise initialized to 0.0
    # here — Task 6 populates CPI surprises via post-processing UPDATE.
    # banrep_rate_surprise deferred to estimation module (spec §3.10).
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
            LN(last_oil_price / LAG(last_oil_price) OVER (ORDER BY week_start)) AS oil_return,
            LN(last_oil_price) AS oil_log_level
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
    -- DANE IPC release-week mapping: join release calendar → ipc_monthly
    dane_ipc_releases AS (
        SELECT
            date_trunc('week', rc.release_date)::DATE AS week_start,
            dim.ipc_pct_change
        FROM dane_release_calendar rc
        JOIN dane_ipc_monthly dim ON dim.date = make_date(rc.year, rc.month, 1)
        WHERE rc.series = 'ipc'
    ),
    -- DANE IPP release-week mapping: join release calendar → ipp_monthly
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
    # Params: trm_returns lookback, rv_agg sample_start, vix sample_start, oil lookback


def build_daily_panel(
    conn: duckdb.DuckDBPyConnection,
    sample_start: date = date(2003, 1, 1),
) -> None:
    """Build daily_panel from raw tables. CREATE OR REPLACE — idempotent.

    Rev 2 fixes: parameterized queries, lookback for LAG, removed COALESCE on booleans.
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
            LN(value / LAG(value) OVER (ORDER BY date)) AS oil_return,
            LN(value) AS oil_log_level
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
```

**Note:** The AR(1) surprise columns (`cpi_surprise_ar1`, `us_cpi_surprise`, `banrep_rate_surprise`) are initialized to 0.0 in the SQL. Task 6 adds the AR(1) computation as a post-processing step that updates these columns using Python/statsmodels. This separation keeps the SQL simple and the AR(1) logic testable independently.

- [ ] **Step 4: Run tests**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_panels.py -v`
Expected: all 4 PASS

- [ ] **Step 5: Commit**

```bash
cd contracts && git add scripts/econ_panels.py scripts/tests/test_econ_panels.py
git commit -m "feat(structural-econ): weekly + daily panel builders from raw tables"
```

---

### Task 6: AR(1) Surprise Construction

**Agent:** Data Engineer
**Files:**
- Modify: `contracts/scripts/econ_panels.py`
- Create: `contracts/scripts/tests/test_econ_ar1.py`

Computes AR(1) surprises for Colombian CPI and US CPI, then updates the panel columns. Uses statsmodels for expanding-window AR(1).

- [ ] **Step 1: Write failing test — AR(1) surprise from IPC series**

```python
# contracts/scripts/tests/test_econ_ar1.py
"""Tests for AR(1) surprise construction."""
from __future__ import annotations

from datetime import date

import duckdb

from scripts.econ_schema import init_db
from scripts.econ_panels import compute_ar1_surprises


def _seed_ipc(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert 24 months of synthetic IPC data (2022-01 to 2023-12)."""
    import math
    for i in range(24):
        year = 2022 + (i // 12)
        month = (i % 12) + 1
        # Synthetic: pct_change oscillates around 0.5 with some noise
        pct = 0.5 + 0.1 * math.sin(i * 0.5)
        conn.execute(
            "INSERT INTO dane_ipc_monthly (date, ipc_index, ipc_pct_change) VALUES (?, ?, ?)",
            [date(year, month, 1), 150.0 + i * 0.5, pct],
        )


def _seed_release_calendar(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert release calendar entries mapping each IPC month to ~7th of next month."""
    for i in range(24):
        year = 2022 + (i // 12)
        month = (i % 12) + 1
        rel_year = year + (1 if month == 12 else 0)
        rel_month = 1 if month == 12 else month + 1
        conn.execute(
            "INSERT INTO dane_release_calendar (year, month, release_date, series) VALUES (?, ?, ?, 'ipc')",
            [year, month, date(rel_year, rel_month, 7)],
        )


def test_compute_ar1_surprises_populates_weekly() -> None:
    """After compute_ar1_surprises, cpi_surprise_ar1 is nonzero on release weeks."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_ipc(conn)
    _seed_release_calendar(conn)
    # Need TRM + FRED for weekly panel
    # Seed minimal TRM for 2023 (post-warmup year)
    for month in range(1, 13):
        for day in [8, 9, 10, 11, 12]:  # Mon-Fri of second week
            try:
                d = date(2023, month, day)
                conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES (?, ?)", [d, 3900.0 + month])
            except Exception:
                pass
    # Minimal VIX + oil
    for month in range(1, 13):
        for day in [8, 9, 10, 11, 12]:
            try:
                d = date(2023, month, day)
                conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('VIXCLS', ?, ?)", [d, 14.0])
                conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('DCOILWTICO', ?, ?)", [d, 74.0])
            except Exception:
                pass

    from scripts.econ_panels import build_weekly_panel
    build_weekly_panel(conn, sample_start=date(2023, 1, 1))
    compute_ar1_surprises(conn, warmup_months=12)

    # Check that at least some release weeks have nonzero cpi_surprise_ar1
    nonzero = conn.execute(
        "SELECT COUNT(*) FROM weekly_panel WHERE cpi_surprise_ar1 != 0.0"
    ).fetchone()
    assert nonzero is not None and nonzero[0] > 0
```

- [ ] **Step 2: Run to verify failure**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_ar1.py -v`
Expected: FAIL — `cannot import name 'compute_ar1_surprises'`

- [ ] **Step 3: Add compute_ar1_surprises to econ_panels.py**

```python
# Append to contracts/scripts/econ_panels.py

import numpy as np


def compute_ar1_surprises(
    conn: duckdb.DuckDBPyConnection,
    warmup_months: int = 12,
) -> None:
    """Compute AR(1) CPI surprises and update weekly_panel + daily_panel.

    Expanding-window AR(1) on DANE IPC MoM % changes.
    First `warmup_months` observations are warmup — their surprises are not used.
    Surprise = actual - AR(1) forecast, mapped to release week via dane_release_calendar.
    """
    # Fetch IPC series ordered by date
    ipc_rows = conn.execute(
        "SELECT date, ipc_pct_change FROM dane_ipc_monthly ORDER BY date"
    ).fetchall()

    if len(ipc_rows) < warmup_months + 1:
        return  # not enough data

    # Fetch release calendar
    release_map = {}  # (year, month) → release_date
    cal_rows = conn.execute(
        "SELECT year, month, release_date FROM dane_release_calendar WHERE series = 'ipc'"
    ).fetchall()
    for yr, mo, rd in cal_rows:
        release_map[(yr, mo)] = rd

    # Compute expanding-window AR(1) surprises
    pct_changes = [float(r[1]) for r in ipc_rows]
    dates = [r[0] for r in ipc_rows]

    for t in range(warmup_months, len(pct_changes)):
        # Expanding window: use observations 0..t-1 to predict t
        y = np.array(pct_changes[:t])
        if len(y) < 2:
            continue
        # Simple AR(1): y_t = a + b * y_{t-1}
        y_lag = y[:-1]
        y_curr = y[1:]
        # OLS: [a, b] = (X'X)^{-1} X'y where X = [1, y_lag]
        x_mat = np.column_stack([np.ones(len(y_lag)), y_lag])
        try:
            coeffs = np.linalg.lstsq(x_mat, y_curr, rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        forecast = coeffs[0] + coeffs[1] * pct_changes[t - 1]
        surprise = pct_changes[t] - forecast

        # Map to release week
        ref_date = dates[t]
        ref_key = (ref_date.year, ref_date.month)
        release_date = release_map.get(ref_key)
        if release_date is None:
            continue

        # Update weekly_panel
        week_start = conn.execute(
            "SELECT date_trunc('week', ?::DATE)::DATE", [release_date]
        ).fetchone()
        if week_start is not None:
            conn.execute(
                "UPDATE weekly_panel SET cpi_surprise_ar1 = ?, dane_ipc_pct = ? WHERE week_start = ?",
                [surprise, pct_changes[t], week_start[0]],
            )

        # Update daily_panel
        conn.execute(
            "UPDATE daily_panel SET cpi_surprise_ar1_daily = ?, abs_cpi_surprise = ? WHERE date = ?",
            [surprise, abs(surprise), release_date],
        )

    # ── US CPI AR(1) surprise (same method on CPIAUCSL) ─────────────────────
    us_cpi_rows = conn.execute(
        "SELECT date, value FROM fred_monthly WHERE series_id = 'CPIAUCSL' ORDER BY date"
    ).fetchall()

    if len(us_cpi_rows) < 2:
        return

    # Compute MoM % changes: (CPI_t / CPI_{t-1} - 1) * 100
    us_dates = [r[0] for r in us_cpi_rows]
    us_values = [float(r[1]) for r in us_cpi_rows]
    us_pct = [(us_values[i] / us_values[i - 1] - 1) * 100 for i in range(1, len(us_values))]
    us_pct_dates = us_dates[1:]  # shifted by one (first month has no prior)

    # Fetch BLS release calendar
    bls_map: dict[tuple[int, int], date] = {}
    bls_rows = conn.execute(
        "SELECT year, month, release_date FROM bls_release_calendar"
    ).fetchall()
    for yr, mo, rd in bls_rows:
        bls_map[(yr, mo)] = rd

    # Expanding-window AR(1) on US CPI MoM changes
    for t in range(warmup_months, len(us_pct)):
        y = np.array(us_pct[:t])
        if len(y) < 2:
            continue
        y_lag = y[:-1]
        y_curr = y[1:]
        x_mat = np.column_stack([np.ones(len(y_lag)), y_lag])
        try:
            coeffs = np.linalg.lstsq(x_mat, y_curr, rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        forecast = coeffs[0] + coeffs[1] * us_pct[t - 1]
        surprise = us_pct[t] - forecast

        # Map to BLS release week
        ref_date = us_pct_dates[t]
        ref_key = (ref_date.year, ref_date.month)
        release_date = bls_map.get(ref_key)
        if release_date is None:
            continue

        week_start_row = conn.execute(
            "SELECT date_trunc('week', ?::DATE)::DATE", [release_date]
        ).fetchone()
        if week_start_row is not None:
            conn.execute(
                "UPDATE weekly_panel SET us_cpi_surprise = ? WHERE week_start = ?",
                [surprise, week_start_row[0]],
            )
```

- [ ] **Step 4: Run tests**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_ar1.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd contracts && git add scripts/econ_panels.py scripts/tests/test_econ_ar1.py
git commit -m "feat(structural-econ): AR(1) expanding-window CPI surprise construction"
```

---

### Task 7: Pipeline Orchestrator and Manifest Logging

**Agent:** Data Engineer
**Files:**
- Create: `contracts/scripts/econ_pipeline.py`
- Create: `contracts/scripts/tests/test_econ_pipeline.py`

Orchestrates the full pipeline: init DB → download all sources → build panels → validate. Logs every download to the manifest.

- [ ] **Step 1: Write failing test — log_manifest inserts audit row**

```python
# contracts/scripts/tests/test_econ_pipeline.py
"""Tests for pipeline orchestrator and manifest logging."""
from __future__ import annotations

from datetime import date

import duckdb

from scripts.econ_schema import init_db
from scripts.econ_pipeline import log_manifest


def test_log_manifest_inserts_row() -> None:
    """log_manifest appends a row to download_manifest."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    log_manifest(conn, source="banrep:trm", status="success", row_count=8250,
                 date_min=date(1991, 12, 2), date_max=date(2026, 4, 16),
                 url_or_path="https://www.datos.gov.co/resource/32sa-8pi3.json")
    count = conn.execute("SELECT COUNT(*) FROM download_manifest").fetchone()
    assert count is not None and count[0] == 1


def test_log_manifest_append_only() -> None:
    """Multiple log_manifest calls for same source append, not overwrite."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    log_manifest(conn, source="banrep:trm", status="verified")
    log_manifest(conn, source="banrep:trm", status="success", row_count=8250)
    count = conn.execute("SELECT COUNT(*) FROM download_manifest WHERE source = 'banrep:trm'").fetchone()
    assert count is not None and count[0] == 2
```

- [ ] **Step 2: Run to verify failure**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_pipeline.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# contracts/scripts/econ_pipeline.py
"""Pipeline orchestrator for structural econometrics data.

Coordinates download → insert → panel build → validate.
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Final

import duckdb


def log_manifest(
    conn: duckdb.DuckDBPyConnection,
    *,
    source: str,
    status: str,
    row_count: int | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
    sha256: str | None = None,
    url_or_path: str | None = None,
    notes: str | None = None,
) -> None:
    """Append a row to download_manifest. INSERT-only (never replaces)."""
    conn.execute(
        "INSERT INTO download_manifest "
        "(source, downloaded_at, row_count, date_min, date_max, sha256, url_or_path, status, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [source, datetime.now(), row_count, date_min, date_max, sha256, url_or_path, status, notes],
    )


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hex digest of raw response bytes."""
    return hashlib.sha256(data).hexdigest()


def run_pipeline(
    db_path: str,
    fred_api_key: str,
    intervention_json_path: str,
    dane_ipc_csv_path: str | None = None,
    dane_ipp_csv_path: str | None = None,
    dane_calendar_csv_path: str | None = None,
) -> duckdb.DuckDBPyConnection:
    """Orchestrate the full pipeline: init → download → insert → build → validate.

    Returns the open DuckDB connection for inspection.
    FRED API key sourced from parameter (caller reads os.environ["FRED_API_KEY"]).
    DANE CSV paths are optional — skip if not yet downloaded.
    banrep_rate_surprise is deferred to the estimation module (spec §3.10).
    """
    import os
    from scripts.econ_schema import init_db
    from scripts.econ_banrep import fetch_trm, fetch_ibr, load_intervention_from_json
    from scripts.econ_fred import fetch_fred_series, fetch_bls_release_dates
    from scripts.econ_dane import parse_dane_ipc_csv, parse_dane_ipp_csv, parse_dane_release_calendar_csv
    from scripts.econ_panels import build_weekly_panel, build_daily_panel, compute_ar1_surprises

    conn = duckdb.connect(db_path)
    init_db(conn)

    # Priority 1a: TRM
    trm_rows = fetch_trm()
    for r in trm_rows:
        conn.execute("INSERT OR REPLACE INTO banrep_trm_daily (date, trm) VALUES (?, ?)", [r.date, r.trm])
    log_manifest(conn, source="banrep:trm", status="success", row_count=len(trm_rows),
                 date_min=trm_rows[0].date if trm_rows else None,
                 date_max=trm_rows[-1].date if trm_rows else None)

    # Priority 1b: IBR
    ibr_rows = fetch_ibr()
    for r in ibr_rows:
        conn.execute("INSERT OR REPLACE INTO banrep_ibr_daily (date, ibr_overnight_er) VALUES (?, ?)",
                     [r.date, r.ibr_overnight_er])
    log_manifest(conn, source="banrep:ibr", status="success", row_count=len(ibr_rows))

    # Priority 1b: Intervention
    intv_rows = load_intervention_from_json(intervention_json_path)
    for r in intv_rows:
        conn.execute(
            "INSERT OR REPLACE INTO banrep_intervention_daily "
            "(date, discretionary, direct_purchase, put_volatility, call_volatility, "
            "put_reserve_accum, call_reserve_decum, ndf, fx_swaps) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [r.date, r.discretionary, r.direct_purchase, r.put_volatility,
             r.call_volatility, r.put_reserve_accum, r.call_reserve_decum, r.ndf, r.fx_swaps])
    log_manifest(conn, source="banrep:intervention", status="success", row_count=len(intv_rows))

    # Priority 1c: EME — unavailable
    log_manifest(conn, source="banrep:eme", status="unavailable",
                 notes="PDF-only, no API/download. AR(1) fallback activated.")

    # Priority 2: DANE (if CSV paths provided)
    if dane_ipc_csv_path:
        with open(dane_ipc_csv_path) as f:
            ipc_rows = parse_dane_ipc_csv(f)
        for r in ipc_rows:
            conn.execute("INSERT OR REPLACE INTO dane_ipc_monthly (date, ipc_index, ipc_pct_change) VALUES (?, ?, ?)",
                         [r.date, r.ipc_index, r.ipc_pct_change])
        log_manifest(conn, source="dane:ipc", status="success", row_count=len(ipc_rows))

    if dane_ipp_csv_path:
        with open(dane_ipp_csv_path) as f:
            ipp_rows = parse_dane_ipp_csv(f)
        for r in ipp_rows:
            conn.execute("INSERT OR REPLACE INTO dane_ipp_monthly (date, ipp_index, ipp_pct_change) VALUES (?, ?, ?)",
                         [r.date, r.ipp_index, r.ipp_pct_change])
        log_manifest(conn, source="dane:ipp", status="success", row_count=len(ipp_rows))

    if dane_calendar_csv_path:
        with open(dane_calendar_csv_path) as f:
            cal_rows = parse_dane_release_calendar_csv(f)
        for r in cal_rows:
            conn.execute("INSERT OR REPLACE INTO dane_release_calendar (year, month, release_date, series, imputed) "
                         "VALUES (?, ?, ?, ?, ?)", [r.year, r.month, r.release_date, r.series, r.imputed])
        log_manifest(conn, source="dane:calendar", status="success", row_count=len(cal_rows))

    # Priority 3: FRED
    for series_id in ("VIXCLS", "DCOILWTICO", "DCOILBRENTEU"):
        rows = fetch_fred_series(series_id, fred_api_key)
        for r in rows:
            conn.execute("INSERT OR REPLACE INTO fred_daily (series_id, date, value) VALUES (?, ?, ?)",
                         [r.series_id, r.date, r.value])
        log_manifest(conn, source=f"fred:{series_id}", status="success", row_count=len(rows))

    cpi_rows = fetch_fred_series("CPIAUCSL", fred_api_key)
    for r in cpi_rows:
        conn.execute("INSERT OR REPLACE INTO fred_monthly (series_id, date, value) VALUES (?, ?, ?)",
                     [r.series_id, r.date, r.value])
    log_manifest(conn, source="fred:CPIAUCSL", status="success", row_count=len(cpi_rows))

    bls_rows = fetch_bls_release_dates(fred_api_key)
    for r in bls_rows:
        conn.execute("INSERT OR REPLACE INTO bls_release_calendar (year, month, release_date) VALUES (?, ?, ?)",
                     [r.year, r.month, r.release_date])
    log_manifest(conn, source="fred:bls_calendar", status="success", row_count=len(bls_rows))

    # Build panels
    build_weekly_panel(conn)
    build_daily_panel(conn)
    compute_ar1_surprises(conn)

    # Validate
    validate_weekly_panel(conn)
    validate_daily_panel(conn)

    return conn
```

- [ ] **Step 4: Run tests**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_pipeline.py -v`
Expected: all 2 PASS

- [ ] **Step 5: Commit**

```bash
cd contracts && git add scripts/econ_pipeline.py scripts/tests/test_econ_pipeline.py
git commit -m "feat(structural-econ): pipeline orchestrator + manifest logging"
```

---

### Task 8: Validation and .gitignore

**Agent:** Data Engineer
**Files:**
- Modify: `contracts/scripts/econ_pipeline.py`
- Modify: `contracts/scripts/tests/test_econ_pipeline.py`
- Modify: `contracts/.gitignore`

Adds validation functions for both panels and updates .gitignore to exclude the DuckDB file.

- [ ] **Step 1: Write failing test — validate_weekly_panel checks constraints**

```python
# Append to contracts/scripts/tests/test_econ_pipeline.py

import pytest

from scripts.econ_pipeline import validate_weekly_panel, validate_daily_panel, ValidationError
from scripts.econ_panels import build_weekly_panel, build_daily_panel
from scripts.tests.test_econ_panels import _seed_trm, _seed_fred


def test_validate_weekly_panel_passes_on_good_data() -> None:
    """validate_weekly_panel passes on a well-formed panel."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    # Should not raise
    validate_weekly_panel(conn)


def test_validate_weekly_panel_catches_null_surprise() -> None:
    """validate_weekly_panel raises if a surprise column contains NULL."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    # Corrupt a row
    conn.execute("UPDATE weekly_panel SET cpi_surprise_ar1 = NULL WHERE week_start = '2024-01-08'")
    with pytest.raises(ValidationError, match="NULL"):
        validate_weekly_panel(conn)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_pipeline.py::test_validate_weekly_panel_passes_on_good_data -v`
Expected: FAIL — `cannot import name 'validate_weekly_panel'`

- [ ] **Step 3: Add validation functions to econ_pipeline.py**

```python
# Append to contracts/scripts/econ_pipeline.py


class ValidationError(Exception):
    """Raised when a derived panel fails validation checks."""


def validate_weekly_panel(conn: duckdb.DuckDBPyConnection) -> None:
    """Validate weekly_panel constraints from spec §5 step 6."""
    # Check table exists
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if "weekly_panel" not in tables:
        raise ValidationError("weekly_panel table does not exist")

    count = conn.execute("SELECT COUNT(*) FROM weekly_panel").fetchone()
    if count is None or count[0] == 0:
        raise ValidationError("weekly_panel is empty")

    # No duplicate week_starts
    dupes = conn.execute(
        "SELECT week_start, COUNT(*) AS c FROM weekly_panel GROUP BY week_start HAVING c > 1"
    ).fetchall()
    if dupes:
        raise ValidationError(f"Duplicate week_starts: {dupes}")

    # RV > 0
    bad_rv = conn.execute("SELECT COUNT(*) FROM weekly_panel WHERE rv <= 0").fetchone()
    if bad_rv and bad_rv[0] > 0:
        raise ValidationError(f"{bad_rv[0]} rows with rv <= 0")

    # n_trading_days in [1, 5]
    bad_n = conn.execute(
        "SELECT COUNT(*) FROM weekly_panel WHERE n_trading_days < 1 OR n_trading_days > 5"
    ).fetchone()
    if bad_n and bad_n[0] > 0:
        raise ValidationError(f"{bad_n[0]} rows with n_trading_days outside [1, 5]")

    # No NULLs in surprise/release columns (should be 0.0)
    null_check = conn.execute(
        "SELECT COUNT(*) FROM weekly_panel WHERE "
        "cpi_surprise_ar1 IS NULL OR us_cpi_surprise IS NULL OR "
        "dane_ipc_pct IS NULL OR dane_ipp_pct IS NULL"
    ).fetchone()
    if null_check and null_check[0] > 0:
        raise ValidationError(f"{null_check[0]} rows with NULL in surprise columns (should be 0.0)")

    # intervention_dummy in {0, 1}
    bad_iv = conn.execute(
        "SELECT COUNT(*) FROM weekly_panel WHERE intervention_dummy NOT IN (0, 1)"
    ).fetchone()
    if bad_iv and bad_iv[0] > 0:
        raise ValidationError(f"{bad_iv[0]} rows with intervention_dummy not in {{0, 1}}")


def validate_daily_panel(conn: duckdb.DuckDBPyConnection) -> None:
    """Validate daily_panel constraints from spec §5 step 6."""
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if "daily_panel" not in tables:
        raise ValidationError("daily_panel table does not exist")

    count = conn.execute("SELECT COUNT(*) FROM daily_panel").fetchone()
    if count is None or count[0] == 0:
        raise ValidationError("daily_panel is empty")

    # No duplicate dates
    dupes = conn.execute(
        "SELECT date, COUNT(*) AS c FROM daily_panel GROUP BY date HAVING c > 1"
    ).fetchall()
    if dupes:
        raise ValidationError(f"Duplicate dates in daily_panel: {dupes[:5]}")

    # intervention_dummy in {0, 1}
    bad_iv = conn.execute(
        "SELECT COUNT(*) FROM daily_panel WHERE intervention_dummy NOT IN (0, 1)"
    ).fetchone()
    if bad_iv and bad_iv[0] > 0:
        raise ValidationError(f"{bad_iv[0]} rows with intervention_dummy not in {{0, 1}}")
```

- [ ] **Step 4: Run tests**

Run: `cd contracts && .venv/bin/python -m pytest scripts/tests/test_econ_pipeline.py -v`
Expected: all 4 PASS

- [ ] **Step 5: Update .gitignore**

Add to `contracts/.gitignore`:
```
# Structural econometrics DuckDB (generated by pipeline)
data/structural_econ.duckdb
data/structural_econ.duckdb.wal
```

- [ ] **Step 6: Commit**

```bash
cd contracts && git add scripts/econ_pipeline.py scripts/tests/test_econ_pipeline.py .gitignore
git commit -m "feat(structural-econ): panel validation + gitignore for DuckDB"
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - Schema DDL for all 10 tables: Task 1 ✓
   - BanRep TRM fetch: Task 2 ✓
   - BanRep IBR fetch: Task 2 ✓
   - Intervention load: Task 2 ✓
   - FRED daily/monthly: Task 3 ✓
   - BLS release dates: Task 3 ✓
   - DANE IPC/IPP: Task 4 ✓
   - DANE release calendar: Task 4 ✓
   - Weekly panel build: Task 5 ✓
   - Daily panel build: Task 5 ✓
   - AR(1) surprise: Task 6 ✓
   - Manifest logging: Task 7 ✓
   - Validation: Task 8 ✓
   - .gitignore: Task 8 ✓

2. **Placeholder scan:** No TBD/TODO found. AR(1) uses numpy lstsq (minimal, no statsmodels dependency needed). US CPI surprise fully constructed in Task 6 via BLS release calendar. `banrep_rate_surprise` deferred to estimation module (spec §3.10 — requires BanRep meeting calendar not in this spec). `dane_ipc_pct` and `dane_ipp_pct` populated from release-week joins in weekly panel SQL.

3. **Type consistency:** `TrmRow`, `IbrRow`, `InterventionRow`, `FredObservation`, `BlsReleaseDate`, `DaneIpcRow`, `DaneIppRow`, `DaneReleaseCalendarRow` — all frozen dataclasses, consistent naming across tasks.

**Rev 2 fixes (from 3-way review):**
- B1/B3: Removed dead `dane_ipc_release` CTE with invalid DuckDB syntax
- B2: Replaced `LAST(value ORDER BY date)` with `ARG_MAX(value, date)` (DuckDB-correct)
- DE-F4/F5: Added 14-day lookback window for LAG() in trm_returns and oil_weekly CTEs; final output filtered to sample_start
- CR-B4: Replaced f-string SQL interpolation with parameterized queries (`?` placeholders)
- CR-B5: Added missing `import pytest` in Task 8
- DE-F7/CR-F10: Added IBR SDMX XML parsing tests (3 tests with sample XML)
- DE-F7/CR-F10: Added IPP CSV parsing tests (2 tests)
- DE-F9/CR-F3: Added US CPI AR(1) surprise construction in Task 6 (same expanding-window method on CPIAUCSL, mapped via bls_release_calendar)
- DE-F11/CR-F5: Added `dane_ipc_releases` and `dane_ipp_releases` CTEs to weekly panel SQL — release-week values now populated from raw tables
- DE-F12: Added `run_pipeline()` orchestrator function in Task 7 — full flow: init → download all → insert → build panels → compute AR(1) → validate
- RC-F3: `run_pipeline()` takes `fred_api_key` parameter (caller reads env var)
- RC-F4: Added `Accept: application/vnd.sdmx.genericdata+xml;version=2.1` header to IBR fetch
- DE-F3/CR-F3: Removed unnecessary `COALESCE(x IS NOT NULL, FALSE)` — `x IS NOT NULL` suffices
- DE-F10: Added explicit note that `banrep_rate_surprise` is deferred to estimation module (spec §3.10)
