"""Pure-function panel-builder for Task 11.O Rev-2 Phase 5a (Data Engineer).

Purpose
-------
Construct each of the 14 resolution-matrix rows declared in the spec
(``contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`` §6) as a
single, deterministic, joint-nonzero pandas DataFrame ready for Analytics
Reporter consumption (OLS+HAC fit + bootstrap reconciliation downstream in
Phase 5b).

Design constraints (per project memory)
---------------------------------------
* All-data-in-DuckDB invariant: this module reads exclusively from the
  caller-supplied ``duckdb.DuckDBPyConnection``. No Dune calls, no FRED
  network calls, no notebook side-effects.
* Frozen dataclasses, free pure functions, full typing
  (per ``functional-python`` skill).
* Friday-anchor invariant: every panel row in the returned DataFrame has a
  Friday week_start (isodow=5). The ``weekly_panel`` Monday→Friday
  reconciliation is encapsulated inside :func:`_translate_weekly_panel_to_friday`
  and never leaks to callers.
* No silent column-name drift: the public API names columns that match the
  spec equation (``y3_value``, ``x_d``, ``vix_avg``, ``oil_return``,
  ``us_cpi_surprise``, ``banrep_rate_surprise``, ``fed_funds_weekly``,
  ``intervention_dummy``) byte-exact.
* Validation guard: ``y3_methodology`` must be in
  ``scripts.econ_query_api._KNOWN_Y3_METHODOLOGY_TAGS`` — defense-in-depth
  against the silent-empty-tuple footgun closed at Rev-5.3.2 Task 11.O Step 0.

Joint-nonzero filter
--------------------
A row is admitted into the panel iff ALL of:

* ``onchain_xd_weekly.value_usd`` (cast to DOUBLE) > 0 for the requested
  ``proxy_kind``;
* ``onchain_y3_weekly.y3_value`` is present (non-null) for the requested
  ``source_methodology``;
* every requested control column in ``weekly_panel`` ∪ ``weekly_rate_panel``
  is non-null at the matching Friday anchor;
* (optional) ``week_start <= locf_tail_cutoff`` if a cutoff is supplied
  (Row 3 LOCF-tail-excluded sensitivity).

This filter is the SAME pre-committed filter the Reality Checker probe-5
applied at the cutoff sweep in
``contracts/.scratch/2026-04-25-y3-rev532-review-reality-checker.md``. Deviating
from it would change the joint-nonzero counts pre-committed in spec §5
(76 / 65 / 56 / 45 / 47 byte-exact), so the filter is locked.

References
----------
Spec:        contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md
Plan:        contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
RC probe-5:  contracts/.scratch/2026-04-25-y3-rev532-review-reality-checker.md
TDD test:    contracts/scripts/tests/inequality/test_phase5_data_prep.py
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final, Sequence

import duckdb
import pandas as pd

from scripts.econ_query_api import _KNOWN_Y3_METHODOLOGY_TAGS

# ── Spec constants (mirror test pinning) ────────────────────────────────────

PRIMARY_XD_KIND: Final[str] = "carbon_basket_user_volume_usd"

#: Six pre-committed continuous controls for the spec's primary equation
#: (§4.1). Every control must be non-null on every panel row.
SIX_CONTROLS: Final[tuple[str, ...]] = (
    "vix_avg",
    "oil_return",
    "us_cpi_surprise",
    "banrep_rate_surprise",
    "fed_funds_weekly",
    "intervention_dummy",
)

#: Three parsimonious controls (Row 6 — collinearity diagnostic).
THREE_PARSIMONIOUS_CONTROLS: Final[tuple[str, ...]] = (
    "vix_avg",
    "oil_return",
    "intervention_dummy",
)

#: Controls that live in ``weekly_panel`` (Monday-anchored, translated to
#: Friday via the +4-day shift inside :func:`_translate_weekly_panel_to_friday`).
_CONTROLS_IN_WEEKLY_PANEL: Final[frozenset[str]] = frozenset(
    {
        "vix_avg",
        "oil_return",
        "us_cpi_surprise",
        "banrep_rate_surprise",
        "intervention_dummy",
    }
)

#: Controls that live in ``weekly_rate_panel`` (already Friday-anchored).
_CONTROLS_IN_WEEKLY_RATE_PANEL: Final[frozenset[str]] = frozenset(
    {"fed_funds_weekly"}
)


# ── Domain types ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class PanelAuditReport:
    """Per-row data-quality audit summary.

    Emitted by :func:`audit_panel` for inclusion in the manifest table
    (one row per matrix row) and the per-row ``validation.md`` artifact.

    Attributes
    ----------
    n_obs:
        Total panel row count after the joint-nonzero filter.
    n_x_d_nonzero:
        Subset of ``n_obs`` with ``x_d > 0`` (sanity check; must equal
        ``n_obs`` because the build_panel filter requires ``x_d > 0``).
    dt_min, dt_max:
        Earliest and latest week_start (Friday-anchored) on the panel.
    n_null_y3:
        Y₃ non-null count is enforced ``= n_obs`` by the joint-nonzero
        filter; surfaced for defense-in-depth.
    """

    n_obs: int
    n_x_d_nonzero: int
    dt_min: date
    dt_max: date
    n_null_y3: int


# ── Pure helper: SQL-fragment composition ───────────────────────────────────


def _validate_controls(controls: Sequence[str]) -> None:
    """Raise ValueError if any control is unknown to the panel readers."""
    unknown = set(controls) - _CONTROLS_IN_WEEKLY_PANEL - _CONTROLS_IN_WEEKLY_RATE_PANEL
    if unknown:
        raise ValueError(
            f"Unknown control column(s): {sorted(unknown)!r}. "
            f"Admitted controls live in weekly_panel "
            f"{sorted(_CONTROLS_IN_WEEKLY_PANEL)!r} or weekly_rate_panel "
            f"{sorted(_CONTROLS_IN_WEEKLY_RATE_PANEL)!r}."
        )


def _validate_y3_methodology(y3_methodology: str) -> None:
    """Raise ValueError on unknown Y₃ tag (matches econ_query_api guard)."""
    if y3_methodology not in _KNOWN_Y3_METHODOLOGY_TAGS:
        admitted = sorted(_KNOWN_Y3_METHODOLOGY_TAGS)
        raise ValueError(
            f"Unknown Y₃ source_methodology={y3_methodology!r}. "
            f"Admitted tags: {admitted}. "
            "Per Rev-5.3.2 Task 11.O Step-0 default-flip, the admitted set is "
            "frozen in scripts.econ_query_api._KNOWN_Y3_METHODOLOGY_TAGS to "
            "prevent silent-empty results from byte-exact-literal typoes."
        )


def _build_select_columns_sql(controls: Sequence[str]) -> str:
    """Produce the SELECT-clause column list for the joint panel."""
    pieces: list[str] = [
        "xd.week_start AS week_start",
        "y3.y3_value AS y3_value",
        "y3.copm_diff AS copm_diff",
        "y3.brl_diff AS brl_diff",
        "y3.kes_diff AS kes_diff",
        "y3.eur_diff AS eur_diff",
        "TRY_CAST(xd.value_usd AS DOUBLE) AS x_d",
    ]
    for col in controls:
        if col in _CONTROLS_IN_WEEKLY_PANEL:
            pieces.append(f"wp.{col} AS {col}")
        elif col in _CONTROLS_IN_WEEKLY_RATE_PANEL:
            pieces.append(f"wrp.{col} AS {col}")
        else:  # pragma: no cover — caught upstream by _validate_controls
            raise ValueError(f"Unknown control column {col!r}")
    return ", ".join(pieces)


def _build_where_clause(controls: Sequence[str]) -> str:
    """Joint-nonzero filter: x_d > 0 AND every control non-null."""
    clauses: list[str] = ["TRY_CAST(xd.value_usd AS DOUBLE) > 0"]
    for col in controls:
        if col in _CONTROLS_IN_WEEKLY_PANEL:
            clauses.append(f"wp.{col} IS NOT NULL")
        elif col in _CONTROLS_IN_WEEKLY_RATE_PANEL:
            clauses.append(f"wrp.{col} IS NOT NULL")
    return " AND ".join(clauses)


# ── Public API ──────────────────────────────────────────────────────────────


def build_panel(
    conn: duckdb.DuckDBPyConnection,
    *,
    x_d_kind: str,
    y3_methodology: str,
    controls: Sequence[str],
    locf_tail_cutoff: date | None = None,
) -> pd.DataFrame:
    """Construct one resolution-matrix row's panel as a deterministic DataFrame.

    Parameters
    ----------
    conn:
        Open DuckDB connection on ``contracts/data/structural_econ.duckdb``.
        Read-only is sufficient.
    x_d_kind:
        Spec literal for the X_d series — e.g. ``'carbon_basket_user_volume_usd'``
        for Row 1 primary or ``'carbon_basket_arb_volume_usd'`` for Row 7
        diagnostic. The ``onchain_xd_weekly.proxy_kind`` filter byte-exact.
    y3_methodology:
        Spec literal for the Y₃ panel methodology — e.g.
        ``'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable'``
        for Row 1 primary. Must be in ``_KNOWN_Y3_METHODOLOGY_TAGS`` or
        :class:`ValueError` is raised.
    controls:
        Ordered tuple of control column names. Each must live in either
        ``weekly_panel`` or ``weekly_rate_panel``. Use :data:`SIX_CONTROLS`
        for the spec primary or :data:`THREE_PARSIMONIOUS_CONTROLS` for
        Row 6.
    locf_tail_cutoff:
        Optional inclusive upper bound on ``week_start`` — used by Row 3
        (LOCF-tail-excluded; cutoff = ``date(2025, 12, 31)``). When ``None``
        no upper-bound truncation applies.

    Returns
    -------
    pd.DataFrame
        Panel rows ordered by ``week_start`` ASC. Columns guaranteed:
        ``week_start`` (date), ``y3_value`` (float), ``x_d`` (float),
        ``copm_diff``, ``brl_diff``, ``kes_diff``, ``eur_diff`` (per-country
        diagnostics; nullable on the 3-country-KE-unavailable methodology),
        plus every control in ``controls``.

    Raises
    ------
    ValueError
        If ``y3_methodology`` is not in the admitted tag set, or if any
        ``controls`` entry is not a known column in either panel.
    """
    _validate_y3_methodology(y3_methodology)
    _validate_controls(controls)

    select_cols = _build_select_columns_sql(controls)
    where = _build_where_clause(controls)

    params: list[object] = [x_d_kind, y3_methodology]
    cutoff_clause = ""
    if locf_tail_cutoff is not None:
        cutoff_clause = " AND xd.week_start <= ?"
        params.append(locf_tail_cutoff)

    sql = f"""
        WITH xd AS (
            SELECT week_start, value_usd, is_partial_week, proxy_kind
            FROM onchain_xd_weekly
            WHERE proxy_kind = ?
        ),
        y3 AS (
            SELECT week_start, y3_value, copm_diff, brl_diff, kes_diff,
                   eur_diff, source_methodology
            FROM onchain_y3_weekly
            WHERE source_methodology = ?
        ),
        wp_friday AS (
            SELECT (week_start + INTERVAL 4 DAY)::DATE AS week_start,
                   vix_avg, oil_return, us_cpi_surprise,
                   banrep_rate_surprise, intervention_dummy,
                   is_cpi_release_week, is_ppi_release_week
            FROM weekly_panel
        )
        SELECT {select_cols}
        FROM xd
        INNER JOIN y3 USING (week_start)
        LEFT JOIN wp_friday wp USING (week_start)
        LEFT JOIN weekly_rate_panel wrp USING (week_start)
        WHERE {where}{cutoff_clause}
        ORDER BY xd.week_start
    """
    df = conn.execute(sql, params).fetchdf()

    # Ensure week_start is a python ``date`` (DuckDB returns numpy datetime64
    # via fetchdf; downstream tests call ``.isoweekday()`` which is a
    # ``datetime.date`` API).
    if "week_start" in df.columns:
        df["week_start"] = pd.to_datetime(df["week_start"]).dt.date

    return df


def audit_panel(panel: pd.DataFrame) -> PanelAuditReport:
    """Compute the per-row audit summary used by ``manifest.md`` + ``validation.md``.

    The audit is a pure function over the DataFrame returned by
    :func:`build_panel` — it does not re-query DuckDB.
    """
    if panel.empty:
        raise ValueError(
            "audit_panel called on an empty panel; this would mask a "
            "joint-nonzero filter regression. Investigate build_panel."
        )

    n_obs = len(panel)
    n_x_d_nonzero = int((panel["x_d"] > 0).sum())
    dt_min = panel["week_start"].min()
    dt_max = panel["week_start"].max()
    n_null_y3 = int(panel["y3_value"].isnull().sum())

    return PanelAuditReport(
        n_obs=n_obs,
        n_x_d_nonzero=n_x_d_nonzero,
        dt_min=dt_min,
        dt_max=dt_max,
        n_null_y3=n_null_y3,
    )


# ── Parquet writer (DuckDB-native; no pyarrow / fastparquet dependency) ─────


def write_panel_parquet(
    conn: duckdb.DuckDBPyConnection,
    panel: pd.DataFrame,
    output_path: str,
) -> None:
    """Persist a prepared panel DataFrame to a parquet file on disk.

    Uses DuckDB's native ``COPY ... TO ... (FORMAT PARQUET)`` so we do not
    need pyarrow or fastparquet (neither is installed in the contracts venv).
    """
    if panel.empty:
        raise ValueError(
            "write_panel_parquet refuses to write an empty panel; check "
            "build_panel filters before calling."
        )
    # Register the DataFrame as a virtual table on the live connection.
    # Using a unique name avoids leaking state between calls.
    view_name = "_phase5_panel_export_view"
    conn.register(view_name, panel)
    try:
        conn.execute(
            f"COPY (SELECT * FROM {view_name}) TO '{output_path}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        conn.unregister(view_name)
