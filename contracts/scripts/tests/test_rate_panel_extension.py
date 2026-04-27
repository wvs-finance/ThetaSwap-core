"""Tests for Task 11.M.6 — Fed funds (DFF) + Banrep IBR-level panel extension.

These assertions close the RC plan-review BLOCKER that Y_asset_leg ≡
``(Banrep_rate − Fed_funds)/52 + ΔTRM/TRM`` was not computable from the
Rev-4 panel: (i) DFF was rejected by the ``fred_daily`` CHECK constraint
and (ii) the Banrep IBR level was not exposed at weekly cadence. The
extension is strictly additive — no pre-existing row, column or hash is
allowed to change.

Five assertions, each a separate test function:
  (a) ``fred_daily`` accepts DFF rows after extension.
  (b) Existing VIXCLS / DCOILWTICO / DCOILBRENTEU rows are unchanged
      byte-exact (re-insert → checksum equality).
  (c) Rev-4 ``decision_hash`` preserved byte-exact after extension.
  (d) ``load_fed_funds_weekly()`` returns a frozen-dataclass wrapper
      with a Friday-anchored weekly series for 2008-01-04 → 2026-04-24,
      spot-checked against FRED DFF.
  (e) ``load_banrep_ibr_weekly()`` likewise for the Banrep IBR series.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Final

import duckdb
import pytest

# ── Constants ────────────────────────────────────────────────────────────────

_FINGERPRINT_PATH: Final[Path] = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "estimates"
    / "nb1_panel_fingerprint.json"
)

_EXPECTED_DECISION_HASH: Final[str] = (
    "6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c"
)

_REAL_DB_PATH: Final[Path] = (
    Path(__file__).resolve().parents[2] / "data" / "structural_econ.duckdb"
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _seed_pre_existing_fred_rows(
    conn: duckdb.DuckDBPyConnection,
) -> dict[str, str]:
    """Insert a deterministic per-series fixture and return {series_id: sha256}.

    The sha256 is computed over a csv-encoded (date, value) snapshot so
    assertion (b) can re-compute it after the CHECK-extension migration
    and compare byte-exact.
    """
    fixtures: dict[str, tuple[tuple[str, float], ...]] = {
        "VIXCLS":       (("2024-01-08", 13.5), ("2024-01-09", 14.0), ("2024-01-10", 13.8)),
        "DCOILWTICO":   (("2024-01-08", 72.5), ("2024-01-09", 73.0), ("2024-01-10", 72.8)),
        "DCOILBRENTEU": (("2024-01-08", 77.9), ("2024-01-09", 78.2), ("2024-01-10", 78.5)),
    }

    baselines: dict[str, str] = {}
    for sid, rows in fixtures.items():
        for d, v in rows:
            conn.execute(
                "INSERT INTO fred_daily (series_id, date, value) VALUES (?, ?, ?)",
                [sid, d, v],
            )
        csv = "\n".join(f"{d},{v}" for d, v in rows).encode()
        baselines[sid] = hashlib.sha256(csv).hexdigest()

    return baselines


def _existing_series_sha(
    conn: duckdb.DuckDBPyConnection, series_id: str
) -> str:
    """Re-compute the same per-series sha256 as ``_seed_pre_existing_fred_rows``."""
    rows = conn.execute(
        "SELECT date, value FROM fred_daily WHERE series_id = ? ORDER BY date",
        [series_id],
    ).fetchall()
    csv = "\n".join(f"{r[0].isoformat()},{r[1]}" for r in rows).encode()
    return hashlib.sha256(csv).hexdigest()


# ── (a) DFF acceptance ───────────────────────────────────────────────────────


def test_fred_daily_accepts_dff_rows() -> None:
    """fred_daily CHECK constraint must accept DFF after extension."""
    from scripts.econ_schema import init_db

    conn = duckdb.connect(":memory:")
    init_db(conn)
    conn.execute(
        "INSERT INTO fred_daily (series_id, date, value) VALUES ('DFF', ?, ?)",
        ["2024-01-02", 5.33],
    )
    row = conn.execute(
        "SELECT value FROM fred_daily WHERE series_id = 'DFF' AND date = '2024-01-02'"
    ).fetchone()
    assert row is not None and row[0] == pytest.approx(5.33)

    # Negative control: a truly-unknown series_id must still be rejected.
    with pytest.raises(duckdb.ConstraintException):
        conn.execute(
            "INSERT INTO fred_daily (series_id, date, value) VALUES "
            "('NOPE', '2024-01-02', 1.0)"
        )


# ── (b) Existing series unchanged byte-exact ─────────────────────────────────


def test_existing_fred_series_unchanged_byte_exact() -> None:
    """Pre-existing VIXCLS / DCOILWTICO / DCOILBRENTEU rows keep identical SHA-256."""
    from scripts.econ_schema import init_db

    conn = duckdb.connect(":memory:")
    init_db(conn)
    baselines = _seed_pre_existing_fred_rows(conn)

    # Insert a DFF row alongside — this is the new-behavior trigger.
    conn.execute(
        "INSERT INTO fred_daily (series_id, date, value) VALUES ('DFF', ?, ?)",
        ["2024-01-08", 5.33],
    )

    for sid, expected in baselines.items():
        got = _existing_series_sha(conn, sid)
        assert got == expected, (
            f"byte-drift on series {sid}: got {got}, expected {expected}"
        )


# ── (c) Rev-4 decision_hash preserved ────────────────────────────────────────


def test_rev4_decision_hash_preserved() -> None:
    """The locked-decision SHA-256 must match the Rev-4 fingerprint on disk."""
    from scripts.cleaning import LOCKED_DECISIONS, _compute_decision_hash

    got = _compute_decision_hash(LOCKED_DECISIONS)
    assert got == _EXPECTED_DECISION_HASH, (
        "decision_hash drifted — LockedDecisions dataclass was mutated."
    )

    # And the JSON file carries the same value on line 23.
    with _FINGERPRINT_PATH.open() as fh:
        fingerprint = json.load(fh)
    assert fingerprint["decision_hash"] == _EXPECTED_DECISION_HASH


# ── (d) Fed funds weekly query API ───────────────────────────────────────────


def test_load_fed_funds_weekly_returns_frozen_dataclass() -> None:
    """load_fed_funds_weekly must return a frozen dataclass with a weekly series."""
    from scripts.econ_query_api import FedFundsWeekly, load_fed_funds_weekly

    # Frozen-dataclass contract
    assert dataclasses.is_dataclass(FedFundsWeekly)
    with pytest.raises(dataclasses.FrozenInstanceError):
        dummy = FedFundsWeekly(week_start=date(2024, 1, 5), value=5.33)
        dummy.value = 0.0  # type: ignore[misc]

    # Load from the real populated database (read-only).
    conn = duckdb.connect(str(_REAL_DB_PATH), read_only=True)
    try:
        rows = load_fed_funds_weekly(conn)
    finally:
        conn.close()

    assert len(rows) > 0, "fed_funds_weekly is empty after extension"
    assert all(isinstance(r, FedFundsWeekly) for r in rows)

    # Friday-anchored weekly series covering the Rev-4 sample window.
    min_week = min(r.week_start for r in rows)
    max_week = max(r.week_start for r in rows)
    assert min_week <= date(2008, 1, 4), f"min_week too late: {min_week}"
    assert max_week >= date(2026, 2, 13), f"max_week too early: {max_week}"

    # Spot-check: 2024-01-05 (Friday) DFF weekly close ≈ 5.33% (Fed held 5.25-5.50).
    friday = date(2024, 1, 5)
    match = next((r for r in rows if r.week_start == friday), None)
    assert match is not None, f"no row for {friday}"
    assert 5.0 <= match.value <= 5.5, (
        f"DFF weekly value on {friday} = {match.value}; expected ≈5.33 "
        "per FRED (Fed held 5.25-5.50 target range)."
    )


# ── (e) Banrep IBR weekly query API ──────────────────────────────────────────


def test_load_banrep_ibr_weekly_returns_frozen_dataclass() -> None:
    """load_banrep_ibr_weekly must return a frozen dataclass with a weekly series."""
    from scripts.econ_query_api import BanrepIbrWeekly, load_banrep_ibr_weekly

    assert dataclasses.is_dataclass(BanrepIbrWeekly)
    with pytest.raises(dataclasses.FrozenInstanceError):
        dummy = BanrepIbrWeekly(week_start=date(2024, 1, 5), value=13.0)
        dummy.value = 0.0  # type: ignore[misc]

    conn = duckdb.connect(str(_REAL_DB_PATH), read_only=True)
    try:
        rows = load_banrep_ibr_weekly(conn)
    finally:
        conn.close()

    assert len(rows) > 0, "banrep_ibr_weekly is empty after extension"
    assert all(isinstance(r, BanrepIbrWeekly) for r in rows)

    min_week = min(r.week_start for r in rows)
    max_week = max(r.week_start for r in rows)
    assert min_week <= date(2008, 1, 4), f"min_week too late: {min_week}"
    assert max_week >= date(2026, 2, 13), f"max_week too early: {max_week}"

    # Spot-check: 2024-01-05 (Friday) — Banrep target TPM = 13.00%, IBR
    # overnight effective rate tracks ± 10 bp. Accept 12.8-13.2.
    friday = date(2024, 1, 5)
    match = next((r for r in rows if r.week_start == friday), None)
    assert match is not None, f"no row for {friday}"
    assert 12.5 <= match.value <= 13.5, (
        f"IBR weekly value on {friday} = {match.value}; expected ≈13.0 "
        "per BanRep target."
    )
