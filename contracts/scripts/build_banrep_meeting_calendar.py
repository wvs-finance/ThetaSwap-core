"""Build the `banrep_meeting_calendar` table.

Source of truth: Banrep SDMX dataflow ``DF_CBR_DAILY_HIST`` (Tasa de Política
Monetaria, daily historical series). A rate-decision meeting day is any date
on which the TPM step-function level changes. This yields the authoritative
set of rate-change meetings over 2008-present.

No-change (hold) meetings are not captured from the TPM series alone and are
not required for the `banrep_rate_surprise` event-study operator, which is
identically zero on hold meetings (research doc 2026-04-18 §5.3).

Usage (standalone):
    .venv/bin/python scripts/build_banrep_meeting_calendar.py

Usage (programmatic):
    import duckdb
    from scripts.build_banrep_meeting_calendar import build_banrep_meeting_calendar

    conn = duckdb.connect('data/structural_econ.duckdb')
    n_inserted = build_banrep_meeting_calendar(conn)
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import duckdb

# Allow running as a script from the ``contracts/`` directory.
_CONTRACTS_DIR = Path(__file__).resolve().parent.parent
if str(_CONTRACTS_DIR) not in sys.path:
    sys.path.insert(0, str(_CONTRACTS_DIR))

from scripts.econ_banrep import (  # noqa: E402
    MeetingRow,
    derive_hold_meetings,
    derive_meetings_from_tpm,
    fetch_tpm,
)
from scripts.econ_pipeline import log_manifest  # noqa: E402
from scripts.econ_schema import init_db  # noqa: E402


def build_banrep_meeting_calendar(
    conn: duckdb.DuckDBPyConnection,
    start_year: int = 2008,
    end_year: int = 2027,
) -> int:
    """Fetch TPM daily history, derive meeting days, upsert into calendar.

    Two-source composition:
      • Primary (Path A, research doc §5.3): TPM-change effective dates from
        Banrep SDMX DF_CBR_DAILY_HIST — every rate-change meeting,
        authoritative and verifiable.
      • Supplemental (Path B, cadence model): hold-meeting dates generated
        from the Junta Directiva institutional schedule (monthly 2008-2012,
        8/year 2013+). De-duplicated by calendar week against rate-change
        meetings so the per-week ``banrep_rate_surprise`` aggregation is
        unaffected.

    Returns the number of meeting rows written to ``banrep_meeting_calendar``.
    Idempotent: uses ``INSERT OR REPLACE`` so re-runs refresh in place.
    """
    init_db(conn)

    tpm_rows = fetch_tpm(start_year=start_year, end_year=end_year)
    if not tpm_rows:
        log_manifest(
            conn,
            source="banrep:tpm_cbr_daily_hist",
            status="empty",
            url_or_path=(
                "https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/"
                "ESTAT,DF_CBR_DAILY_HIST,1.0/all/ALL/"
            ),
            notes="empty TPM response — meeting-calendar build aborted",
        )
        return 0

    rate_change_meetings = derive_meetings_from_tpm(tpm_rows)

    # Cap the hold-meeting cadence at the latest real TPM observation so we do
    # not generate speculative future meeting dates beyond the IBR/TPM data
    # currently available.
    last_tpm_date = max(r.date for r in tpm_rows)
    hold_meetings = [
        m for m in derive_hold_meetings(
            rate_change_meetings,
            start_year=start_year,
            end_year=last_tpm_date.year,
        )
        if m.meeting_date <= last_tpm_date
    ]

    all_meetings: list[MeetingRow] = rate_change_meetings + hold_meetings
    _upsert_meetings(conn, all_meetings)

    log_manifest(
        conn,
        source="banrep:tpm_cbr_daily_hist",
        status="verified",
        row_count=len(all_meetings),
        date_min=min(m.meeting_date for m in all_meetings) if all_meetings else None,
        date_max=max(m.meeting_date for m in all_meetings) if all_meetings else None,
        url_or_path=(
            "https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/"
            "ESTAT,DF_CBR_DAILY_HIST,1.0/all/ALL/"
        ),
        notes=(
            f"{len(rate_change_meetings)} rate-change + "
            f"{len(hold_meetings)} inferred-hold meeting rows "
            f"(TPM obs={len(tpm_rows)})"
        ),
    )
    return len(all_meetings)


def _upsert_meetings(
    conn: duckdb.DuckDBPyConnection,
    meetings: list[MeetingRow],
) -> None:
    """Insert or replace MeetingRow records into banrep_meeting_calendar."""
    for m in meetings:
        conn.execute(
            "INSERT OR REPLACE INTO banrep_meeting_calendar "
            "(year, meeting_date, meeting_type) VALUES (?, ?, ?)",
            [m.year, m.meeting_date, m.meeting_type],
        )


if __name__ == "__main__":  # pragma: no cover — entrypoint
    db_path = _CONTRACTS_DIR / "data" / "structural_econ.duckdb"
    if not db_path.exists():
        raise SystemExit(f"DuckDB not found at {db_path}")
    connection = duckdb.connect(str(db_path))
    try:
        n = build_banrep_meeting_calendar(connection)
        print(f"banrep_meeting_calendar: upserted {n} rate-change meeting rows")
        min_d, max_d = connection.execute(
            "SELECT MIN(meeting_date), MAX(meeting_date) FROM banrep_meeting_calendar"
        ).fetchone() or (None, None)
        print(f"  coverage: {min_d} → {max_d}")
    finally:
        connection.close()
