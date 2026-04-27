"""TDD tests for Rev-5.1 Task 11.N — X_d weekly filter + B2B/B2C classifier.

Plan:   contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md @ 8c984ab56
Memo:   contracts/.scratch/2026-04-24-xd-filter-design-memo.md

Public API under test (per memo §8)::

    def classify_addresses(
        activity_rows: tuple[OnchainCopmAddressActivity, ...],
        top_edges: tuple[OnchainCopmTopEdge, ...],
        *,
        known_hubs: frozenset[str],
        top_n_by_activity: int = 50,
        min_outbound_for_distributor: int = 10,
        top_n_edges: int = 10,
    ) -> tuple[frozenset[str], frozenset[str]]:
        ...

    def compute_weekly_xd(
        daily_flow_rows: tuple[OnchainCcopDailyFlow, ...],
        *,
        friday_anchor_tz: str = "America/Bogota",
    ) -> WeeklyXdPanel:
        ...

    @dataclass(frozen=True, slots=True)
    class WeeklyXdPanel:
        weeks: tuple[date, ...]
        values_usd: tuple[float, ...]
        is_partial_week: tuple[bool, ...]
        b2b_addresses: frozenset[str]
        b2c_addresses: frozenset[str]
        proxy_kind: str


Five assertion groups, all using real DuckDB data (no mocks):

  (i)   GOLDEN FIXTURE — compute_weekly_xd() emits the pre-committed
        value 8542.188243 USD for the week ending Friday 2025-10-31
        (Monday 2025-10-27 → Sunday 2025-11-02).  Value was derived by
        an independent SQL pass at memo-authoring time and pinned here
        BEFORE implementation existed.

  (ii)  INDEPENDENT-REPRODUCTION WITNESS — a second code path computes
        the same value via raw SQL and compares to compute_weekly_xd()
        to 6-decimal USD precision. This guards against silent-test-pass
        (impl and test sharing the same bug) per the Phase-A.0 3-integration-
        test guard catalogued in memory `project_fx_vol_econ_reviewer_and_
        silent_test_pass_lessons`.

  (iii) FROZEN-DATACLASS CONTRACT — WeeklyXdPanel is @dataclass(frozen=True);
        attempting to mutate an instance raises FrozenInstanceError.

  (iv)  PURITY — calling classify_addresses() twice with the same inputs
        yields identical output and does not mutate its input collections.
        Similarly for compute_weekly_xd().

  (v)   DETERMINISM — running the full pipeline twice against the same
        DuckDB state produces byte-identical WeeklyXdPanel instances.

The tests MUST fail on ImportError until
``contracts/scripts/copm_xd_filter.py`` exists with the committed
public API. This is the strict-TDD Red phase.

Pre-commitment hygiene: the golden value 8542.188243 was locked BEFORE
the implementation was authored. The value was computed by the memo-
authoring agent using a direct Decimal-precision SQL sum against
``onchain_copm_ccop_daily_flow`` over dates [2025-10-27, 2025-11-02].
No threshold or output of the implementation-under-test has been
observed to derive this constant.
"""
from __future__ import annotations

import dataclasses
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Final

import duckdb
import pytest

# ── Pre-committed golden fixture (pinned by memo §4, independently computed) ──

# Week anchor (ISO-week Friday) — matches Task 11.B convention.
GOLDEN_FRIDAY: Final[date] = date(2025, 10, 31)
GOLDEN_MONDAY: Final[date] = date(2025, 10, 27)
GOLDEN_SUNDAY: Final[date] = date(2025, 11, 2)

# X_d expected value in USD (6-decimal precision preserved).
GOLDEN_XD_USD: Final[Decimal] = Decimal("8542.188243")

# Panel window bounds per memo §2.2.
PANEL_MIN_DATE: Final[date] = date(2024, 9, 17)
PANEL_MAX_DATE: Final[date] = date(2026, 4, 24)

# Known-hub addresses pre-committed in memo §3.1.  Full 42-char values
# resolved against ``onchain_copm_address_activity_top400`` by matching
# the 11.M profile shorthand (``0x0155b191...5ccf1fe5`` and
# ``0x5bd35ee3...cfc122``) — the profile's shorthand is a structural
# identifier (profile §3 row #1 and §8 "distribution hub"); the full
# hex is the only thing that lets the classifier key them.
KNOWN_HUBS: Final[frozenset[str]] = frozenset({
    "0x0155b191ec52728d26b1cd82f6a412d5d6897c04",   # primary treasury
    "0x5bd35ee3c1975b2d735d2023bd4f38e3b0cfc122",   # 2025 distribution hub
})

# ── Path plumbing ──

_CONTRACTS_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
_REAL_DB_PATH: Final[Path] = _CONTRACTS_ROOT / "data" / "structural_econ.duckdb"


# ── Session fixture: read-only DuckDB ──


@pytest.fixture(scope="module")
def xd_conn() -> duckdb.DuckDBPyConnection:
    """Module-scoped read-only connection to the real structural-econ DuckDB.

    We deliberately do not reuse the session-scoped ``conn`` fixture from
    ``tests/conftest.py`` — this test family is self-contained and should
    remain runnable in isolation (``pytest scripts/tests/inequality``).
    """
    assert _REAL_DB_PATH.is_file(), (
        f"structural_econ.duckdb missing at {_REAL_DB_PATH}. "
        "Task 11.M.5 migration must be run first."
    )
    connection = duckdb.connect(str(_REAL_DB_PATH), read_only=True)
    try:
        yield connection
    finally:
        connection.close()


# ── (i) GOLDEN FIXTURE ────────────────────────────────────────────────────


def test_compute_weekly_xd_matches_golden_fixture(
    xd_conn: duckdb.DuckDBPyConnection,
) -> None:
    """compute_weekly_xd() must emit the pre-committed USD value for the
    week ending Friday 2025-10-31."""
    from scripts.copm_xd_filter import compute_weekly_xd
    from scripts.econ_query_api import load_onchain_daily_flow

    daily = load_onchain_daily_flow(xd_conn)
    panel = compute_weekly_xd(daily)

    # Locate the row for the golden Friday.
    idx = panel.weeks.index(GOLDEN_FRIDAY)
    actual = Decimal(str(panel.values_usd[idx])).quantize(Decimal("0.000001"))

    assert actual == GOLDEN_XD_USD, (
        f"X_d mismatch at {GOLDEN_FRIDAY}: expected {GOLDEN_XD_USD}, "
        f"got {actual} (raw float={panel.values_usd[idx]!r})"
    )
    # This week falls fully inside the panel window [2024-09-17, 2026-04-24]
    assert panel.is_partial_week[idx] is False


# ── (ii) INDEPENDENT-REPRODUCTION WITNESS ─────────────────────────────────


def test_witness_matches_compute_weekly_xd(
    xd_conn: duckdb.DuckDBPyConnection,
) -> None:
    """A raw-SQL witness path must agree with compute_weekly_xd() for the
    golden week to the cent."""
    from scripts.copm_xd_filter import compute_weekly_xd
    from scripts.econ_query_api import load_onchain_daily_flow

    # Witness: raw SQL sum of VARCHAR USD columns for the golden week.
    # No Python imports from the module-under-test here — deliberately
    # a parallel code path to catch shared-bug silent-test-pass.
    witness_rows = xd_conn.execute(
        """
        SELECT date, copm_mint_usd, copm_burn_usd
        FROM onchain_copm_ccop_daily_flow
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        """,
        [GOLDEN_MONDAY, GOLDEN_SUNDAY],
    ).fetchall()
    assert len(witness_rows) == 7, (
        f"Expected 7 daily rows for golden week, got {len(witness_rows)}"
    )
    witness_mint = sum((Decimal(r[1]) for r in witness_rows), Decimal("0"))
    witness_burn = sum((Decimal(r[2]) for r in witness_rows), Decimal("0"))
    witness_xd = witness_mint - witness_burn

    # Module-under-test path.
    daily = load_onchain_daily_flow(xd_conn)
    panel = compute_weekly_xd(daily)
    idx = panel.weeks.index(GOLDEN_FRIDAY)
    module_xd = Decimal(str(panel.values_usd[idx])).quantize(Decimal("0.000001"))

    assert module_xd == witness_xd.quantize(Decimal("0.000001")), (
        f"Witness disagreement: SQL={witness_xd}, module={module_xd}"
    )


# ── (iii) FROZEN-DATACLASS CONTRACT ───────────────────────────────────────


def test_weekly_xd_panel_is_frozen_dataclass(
    xd_conn: duckdb.DuckDBPyConnection,
) -> None:
    """WeeklyXdPanel must be a frozen dataclass with the committed field set."""
    from scripts.copm_xd_filter import WeeklyXdPanel, compute_weekly_xd
    from scripts.econ_query_api import load_onchain_daily_flow

    assert dataclasses.is_dataclass(WeeklyXdPanel), (
        "WeeklyXdPanel must be a @dataclass"
    )
    # dataclasses.fields reliably reflects the declared field set regardless
    # of slots/frozen flags.
    field_names = {f.name for f in dataclasses.fields(WeeklyXdPanel)}
    expected = {
        "weeks",
        "values_usd",
        "is_partial_week",
        "b2b_addresses",
        "b2c_addresses",
        "proxy_kind",
    }
    assert field_names == expected, (
        f"Expected fields {expected}, got {field_names}"
    )

    # Frozen semantics: attribute assignment on an instance must raise.
    daily = load_onchain_daily_flow(xd_conn)
    panel = compute_weekly_xd(daily)
    with pytest.raises(dataclasses.FrozenInstanceError):
        panel.proxy_kind = "mutated"  # type: ignore[misc]

    # Committed proxy_kind default surfaces the X_D_INSUFFICIENT_DATA
    # escalation to every downstream consumer.
    assert panel.proxy_kind == "net_primary_issuance_usd"


# ── (iv) PURITY ───────────────────────────────────────────────────────────


def test_classify_addresses_is_pure(
    xd_conn: duckdb.DuckDBPyConnection,
) -> None:
    """classify_addresses: no input mutation, deterministic output."""
    from scripts.copm_xd_filter import classify_addresses
    from scripts.econ_query_api import (
        load_onchain_copm_address_activity,
        load_onchain_copm_top100_edges,
    )

    activity = load_onchain_copm_address_activity(xd_conn)
    edges = load_onchain_copm_top100_edges(xd_conn)

    before_activity = tuple(activity)
    before_edges = tuple(edges)

    b2b_1, b2c_1 = classify_addresses(activity, edges, known_hubs=KNOWN_HUBS)
    b2b_2, b2c_2 = classify_addresses(activity, edges, known_hubs=KNOWN_HUBS)

    # Deterministic.
    assert b2b_1 == b2b_2
    assert b2c_1 == b2c_2

    # Frozensets are immutable.
    assert isinstance(b2b_1, frozenset)
    assert isinstance(b2c_1, frozenset)

    # Inputs unchanged.
    assert tuple(activity) == before_activity
    assert tuple(edges) == before_edges

    # Non-empty partition sanity — the B2B set must contain at least the
    # known hubs (which are also in the top-50 activity universe); the B2C
    # set must not be empty (long-tail retail exists per 11.M profile).
    for hub in KNOWN_HUBS:
        assert hub in b2b_1, f"Known hub {hub} missing from B2B set"
    assert len(b2c_1) > 0

    # Partition discipline: a classified address is in exactly one set.
    assert b2b_1.isdisjoint(b2c_1)


def test_compute_weekly_xd_is_pure(
    xd_conn: duckdb.DuckDBPyConnection,
) -> None:
    """compute_weekly_xd: no input mutation, no side effects."""
    from scripts.copm_xd_filter import compute_weekly_xd
    from scripts.econ_query_api import load_onchain_daily_flow

    daily = load_onchain_daily_flow(xd_conn)
    before = tuple(daily)

    panel_1 = compute_weekly_xd(daily)
    panel_2 = compute_weekly_xd(daily)

    # Deterministic output.
    assert panel_1.weeks == panel_2.weeks
    assert panel_1.values_usd == panel_2.values_usd
    assert panel_1.is_partial_week == panel_2.is_partial_week
    assert panel_1.proxy_kind == panel_2.proxy_kind

    # Input unmutated.
    assert tuple(daily) == before


# ── (vi) DuckDB round-trip: onchain_xd_weekly table (Task 11.N Step 5) ─────


def test_onchain_xd_weekly_roundtrip(
    xd_conn: duckdb.DuckDBPyConnection,
) -> None:
    """The ``onchain_xd_weekly`` table must contain a row per Friday with
    a ``value_usd`` matching ``compute_weekly_xd()`` to 6-decimal USD
    precision and the correct ``proxy_kind`` tag.

    Directly exercises the Step-5 persistence path committed by the
    Task 11.N migration-extension (``ingest_onchain_xd_weekly`` +
    ``load_onchain_xd_weekly``).  Guarantees the derived table is
    byte-equal to the in-memory computation that produced it.
    """
    from scripts.copm_xd_filter import PROXY_KIND, compute_weekly_xd
    from scripts.econ_query_api import (
        load_onchain_daily_flow,
        load_onchain_xd_weekly,
    )

    # In-memory compute path.
    daily = load_onchain_daily_flow(xd_conn)
    panel = compute_weekly_xd(daily)

    # Persisted path — filter to the supply-channel proxy_kind since
    # Rev-5.2.1 Task 11.N.1 Step 0 relaxed the CHECK constraint and
    # the distribution-channel (b2b_to_b2c_net_flow_usd) rows now
    # co-exist for the same Friday. This test exercises ONLY the
    # supply-channel round-trip (compute_weekly_xd's contract).
    persisted = load_onchain_xd_weekly(xd_conn, proxy_kind=PROXY_KIND)

    # Row count alignment.
    assert len(persisted) == len(panel.weeks), (
        f"Row count mismatch: table={len(persisted)}, "
        f"compute_weekly_xd={len(panel.weeks)}"
    )

    # Per-row alignment by week_start.
    panel_by_week: dict[date, tuple[float, bool]] = {
        w: (v, p)
        for w, v, p in zip(
            panel.weeks, panel.values_usd, panel.is_partial_week, strict=True
        )
    }
    for row in persisted:
        assert row.week_start in panel_by_week, (
            f"Persisted week {row.week_start} absent from compute output"
        )
        expected_v, expected_p = panel_by_week[row.week_start]
        got = Decimal(str(row.value_usd)).quantize(Decimal("0.000001"))
        want = Decimal(str(expected_v)).quantize(Decimal("0.000001"))
        assert got == want, (
            f"{row.week_start}: persisted {got} != computed {want}"
        )
        assert row.is_partial_week == expected_p
        assert row.proxy_kind == PROXY_KIND

    # Golden anchor exists in the persisted table.
    golden_row = next(
        (r for r in persisted if r.week_start == GOLDEN_FRIDAY), None
    )
    assert golden_row is not None, (
        f"Golden Friday {GOLDEN_FRIDAY} missing from onchain_xd_weekly"
    )
    golden_got = Decimal(str(golden_row.value_usd)).quantize(Decimal("0.000001"))
    assert golden_got == GOLDEN_XD_USD, (
        f"Persisted golden value {golden_got} != {GOLDEN_XD_USD}"
    )


# ── (v) DETERMINISM of full-pipeline composition ────────────────────────────


def test_full_pipeline_determinism(
    xd_conn: duckdb.DuckDBPyConnection,
) -> None:
    """Running the full read → classify → compute pipeline twice yields
    byte-identical WeeklyXdPanel instances."""
    from scripts.copm_xd_filter import (
        WeeklyXdPanel,
        classify_addresses,
        compute_weekly_xd,
    )
    from scripts.econ_query_api import (
        load_onchain_copm_address_activity,
        load_onchain_copm_top100_edges,
        load_onchain_daily_flow,
    )

    def run_once() -> WeeklyXdPanel:
        activity = load_onchain_copm_address_activity(xd_conn)
        edges = load_onchain_copm_top100_edges(xd_conn)
        daily = load_onchain_daily_flow(xd_conn)
        b2b, b2c = classify_addresses(activity, edges, known_hubs=KNOWN_HUBS)
        base = compute_weekly_xd(daily)
        # Attach classifier output to the panel (re-construct via dataclasses.replace).
        return dataclasses.replace(
            base, b2b_addresses=b2b, b2c_addresses=b2c
        )

    first = run_once()
    second = run_once()

    assert first == second, (
        "Full pipeline non-deterministic: dataclasses differ"
    )
    # Extra: structural sanity — at least one non-partial week and some
    # non-zero X_d values exist in the real panel.
    assert any(not pw for pw in first.is_partial_week)
    assert any(v != 0.0 for v in first.values_usd)
