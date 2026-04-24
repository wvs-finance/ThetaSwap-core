"""X_d weekly filter + B2B/B2C classifier for the Abrigo inequality-
differential exercise.

Rev-5.1 Task 11.N.  Pre-commitment design memo:
``contracts/.scratch/2026-04-24-xd-filter-design-memo.md``.

-------------------------------------------------------------------------
X_D_INSUFFICIENT_DATA — ESCALATION FLAG
-------------------------------------------------------------------------

The originally-proposed filter (per-transaction weekly net-flow from
B2B-classified addresses into B2C-classified addresses) **cannot** be
honestly computed from the aggregate tables currently in the structural-
econ DuckDB. The raw 110,069-row ``copm_transfers`` table is present
only as a 10-row SAMPLE (flagged ``is_sample=True`` by the Task 11.M.5
migration) because the Dune MCP pagination budget made a full raw pull
impractical in one agent session.

In its place, this module emits a **surrogate** X_d:

    X_d_t := Σ copm_mint_usd[d]  −  Σ copm_burn_usd[d]    (d ∈ week(t))

— the weekly net primary issuance (USD) of the COPM stablecoin. Rationale:
mints flow 100 % into a single treasury which immediately forwards them
to distribution hubs (see Task 11.M profile §3), so mints proxy B2B→B2C
supply expansion; burns proxy contraction. Oscillation-loop volume
(B2B-internal rebalancing, 52 % of transfer *events* per 11.M §5) is
naturally excluded — it never touches the mint/burn boundary. This
omission is the desired behaviour: Lustig-Roussanov-Verdelhan (2011,
RFS 24(11)) license filtering zero-net-flow high-frequency trading out
of the macro-signal channel.

The ``proxy_kind`` field on :class:`WeeklyXdPanel` is set to
``"net_primary_issuance_usd"`` — downstream consumers MUST NOT claim the
output is a true edge-level B2B→B2C differential.  For the true filter,
a Tier-2 raw-transfers data pull is required (see Task 11.L
``LIT_SPARSE_onchain_inequality`` finding).

-------------------------------------------------------------------------
Public API (pure free functions + one frozen dataclass)
-------------------------------------------------------------------------

* :func:`classify_addresses` — deterministic B2B / B2C partition of the
  300-address activity universe, driven by three pre-committed thresholds
  documented in the design memo §3.
* :func:`compute_weekly_xd` — Friday-anchored, America/Bogota-timezone
  weekly aggregation of net primary issuance.
* :class:`WeeklyXdPanel` — ``@dataclass(frozen=True, slots=True)`` result
  type carrying the week index, values, partial-week flags, classifier
  sets, and the ``proxy_kind`` escalation flag.

Composition is over free functions; no classes except the frozen
dataclass.  See :mod:`scripts.econ_query_api` for the on-chain loader
contracts consumed here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final, Literal

from zoneinfo import ZoneInfo

from scripts.econ_query_api import (
    OnchainCcopDailyFlow,
    OnchainCopmAddressActivity,
    OnchainCopmTopEdge,
)

# ── Constants ───────────────────────────────────────────────────────────────

# Rev-5.1: supply-channel surrogate — Σ mint − Σ burn per Friday-week.
# Rev-5.2.1 Task 11.N.1 Step 0 adds the distribution-channel variant
# ``b2b_to_b2c_net_flow_usd`` (full-transfers panel required to compute).
PROXY_KIND: Final[str] = "net_primary_issuance_usd"

#: Allowed ``proxy_kind`` literal set — mirrored in the
#: ``onchain_xd_weekly`` CHECK constraint (see :mod:`scripts.econ_schema`).
ProxyKindT = Literal["net_primary_issuance_usd", "b2b_to_b2c_net_flow_usd"]

DEFAULT_FRIDAY_ANCHOR_TZ: Final[str] = "America/Bogota"

#: ISO-weekday code for Monday (Python ``date.isoweekday()`` == 1).
_MONDAY_ISO: Final[int] = 1
#: ISO-weekday code for Friday (Python ``date.isoweekday()`` == 5).
_FRIDAY_ISO: Final[int] = 5


# ── Result type ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class WeeklyXdPanel:
    """Friday-anchored weekly X_d panel with auxiliary B2B/B2C address sets.

    Attributes
    ----------
    weeks:
        Tuple of Friday anchor dates (``isoweekday() == 5``).  One per
        observed week in the ingested daily-flow panel.  Sorted ascending.
    values_usd:
        USD-denominated X_d = Σ mint − Σ burn for each week, parallel to
        ``weeks``.  Float with 6-decimal USD precision preserved from the
        Task 11.A CSV source (input is VARCHAR → Decimal → float at read
        time).
    is_partial_week:
        ``True`` when the 7-day Monday-to-Sunday span for that Friday
        extends outside the panel's ``[date_min, date_max]``.  Only
        triggered at the two boundaries.
    b2b_addresses:
        Frozenset of addresses classified as B2B by
        :func:`classify_addresses`.  Auxiliary — NOT used by the weekly-
        X_d computation; downstream consumers may use it for joint
        diagnostics.
    b2c_addresses:
        Frozenset of addresses classified as B2C by
        :func:`classify_addresses`.  Auxiliary — see ``b2b_addresses``.
    proxy_kind:
        Escalation tag.  Committed value
        ``"net_primary_issuance_usd"`` surfaces ``X_D_INSUFFICIENT_DATA``
        to every downstream consumer at runtime.
    """

    weeks: tuple[date, ...]
    values_usd: tuple[float, ...]
    is_partial_week: tuple[bool, ...]
    b2b_addresses: frozenset[str] = frozenset()
    b2c_addresses: frozenset[str] = frozenset()
    proxy_kind: str = PROXY_KIND


# ── Private helpers (free functions) ────────────────────────────────────────


def _normalise_address(raw: str) -> str:
    """Lowercase an Ethereum-style address for set membership.

    All address columns in :mod:`scripts.econ_schema` are checksum-
    agnostic VARCHAR(42); this helper makes case-folding explicit at the
    classifier boundary so a hex-caller cannot accidentally miss a hub
    due to mixed case.
    """
    return raw.lower()


def _friday_of_iso_week(d: date) -> date:
    """Return the Friday of the ISO-week containing ``d`` (isoweekday 5).

    The rule matches ``date_trunc('week', d) + interval '4 days'`` in
    DuckDB: Monday-anchored weeks, Friday offset.  Pure function.
    """
    # Monday of this ISO week:
    monday = d - timedelta(days=d.isoweekday() - _MONDAY_ISO)
    # Friday = Monday + 4 days.
    return monday + timedelta(days=4)


def _week_span(friday: date) -> tuple[date, date]:
    """Return (Monday, Sunday) containing ``friday``.

    ``friday`` must satisfy ``isoweekday() == 5``; violations are caller
    programming errors and raise :class:`AssertionError` in development.
    """
    assert friday.isoweekday() == _FRIDAY_ISO, (
        f"_week_span expects a Friday, got {friday} "
        f"(isoweekday={friday.isoweekday()})"
    )
    monday = friday - timedelta(days=4)
    sunday = friday + timedelta(days=2)
    return monday, sunday


# ── Public API ──────────────────────────────────────────────────────────────


def classify_addresses(
    activity_rows: tuple[OnchainCopmAddressActivity, ...],
    top_edges: tuple[OnchainCopmTopEdge, ...],
    *,
    known_hubs: frozenset[str],
    top_n_by_activity: int = 50,
    min_outbound_for_distributor: int = 10,
    top_n_edges: int = 10,
) -> tuple[frozenset[str], frozenset[str]]:
    """Partition the activity-table address universe into (B2B, B2C).

    Pre-committed classifier rule (see memo §3.1).  An address ``a`` is
    B2B iff **any** of::

        (a) a ∈ known_hubs                                            -- rule (a)
        (b) a is in the top_n_by_activity rows of activity_rows
            (CSV-native order) AND a.n_outbound ≥ min_outbound_for_distributor
                                                                      -- rule (b)
        (c) a is a from_address or to_address of any of the first
            top_n_edges edges in top_edges (CSV-native order, which
            Dune has ordered by n_transfers DESC)                     -- rule (c)

    Otherwise ``a`` is B2C.  Addresses NOT in ``activity_rows`` are
    implicitly long-tail B2C per 11.M profile §8 and are not enumerated.

    Parameters
    ----------
    activity_rows:
        Output of :func:`scripts.econ_query_api.load_onchain_copm_address_activity`
        (300 rows, CSV-native order preserved via ``_csv_row_idx``).
    top_edges:
        Output of :func:`scripts.econ_query_api.load_onchain_copm_top100_edges`
        (100 rows, CSV-native order preserved via ``_csv_row_idx``).
    known_hubs:
        Frozenset of hub addresses (lowercase).  Committed in memo §3.1:
        primary treasury + 2025 distribution hub.
    top_n_by_activity:
        Pre-committed threshold for rule (b).  Default 50 (memo §3.2).
    min_outbound_for_distributor:
        Pre-committed threshold for rule (b).  Default 10 (memo §3.2).
    top_n_edges:
        Pre-committed threshold for rule (c).  Default 10 (memo §3.2).

    Returns
    -------
    tuple[frozenset[str], frozenset[str]]
        (b2b_set, b2c_set).  Disjoint; union equals the lowercased
        address-set of ``activity_rows``.

    Notes
    -----
    Pure function: no mutation of inputs, no I/O, deterministic for
    fixed inputs.  Address comparison is case-folded via
    :func:`_normalise_address` — callers may pass checksum-case hubs.
    """
    # Defensive copies at the set boundary (inputs remain untouched).
    hubs_lower = frozenset(_normalise_address(h) for h in known_hubs)

    # Normalised address universe, CSV-native order preserved.
    activity_lower: list[tuple[str, int]] = [
        (_normalise_address(r.address), r.n_outbound)
        for r in activity_rows
    ]
    universe: frozenset[str] = frozenset(addr for addr, _ in activity_lower)

    b2b_accum: set[str] = set()

    # Rule (a) — known hubs (restricted to the activity universe; hubs
    # outside the 300-row universe are not enumerable here).
    b2b_accum |= (hubs_lower & universe)

    # Rule (b) — top N activity rows with n_outbound ≥ threshold.
    for addr, n_out in activity_lower[:top_n_by_activity]:
        if n_out >= min_outbound_for_distributor:
            b2b_accum.add(addr)

    # Rule (c) — endpoints of the top N edges (both sides).
    for edge in top_edges[:top_n_edges]:
        ep_from = _normalise_address(edge.from_address)
        ep_to = _normalise_address(edge.to_address)
        # Only include endpoints that are in the activity universe —
        # otherwise we'd return addresses without n_inbound/n_outbound
        # metadata and break the disjoint-union contract below.
        if ep_from in universe:
            b2b_accum.add(ep_from)
        if ep_to in universe:
            b2b_accum.add(ep_to)

    b2b_set: frozenset[str] = frozenset(b2b_accum)
    b2c_set: frozenset[str] = universe - b2b_set

    return b2b_set, b2c_set


def compute_weekly_xd(
    daily_flow_rows: tuple[OnchainCcopDailyFlow, ...],
    *,
    friday_anchor_tz: str = DEFAULT_FRIDAY_ANCHOR_TZ,
    proxy_kind: ProxyKindT = PROXY_KIND,
) -> WeeklyXdPanel:
    """Aggregate daily (mint − burn) USD into Friday-anchored weekly X_d.

    Rule: for every Friday ``t`` touched by the daily panel, sum
    ``copm_mint_usd − copm_burn_usd`` across the 7 days Monday(t) through
    Sunday(t).  Weeks whose [Monday, Sunday] span extends outside the
    panel window ``[date_min, date_max]`` carry ``is_partial_week=True``.

    The ``friday_anchor_tz`` keyword is accepted for API parity with
    Task 11.B; the daily-flow rows are already date-only (no intraday
    timestamps), so timezone does not affect the bucketing in this
    proxy.  The parameter is validated (must be a recognisable IANA
    zone) to fail fast if a caller passes garbage.

    Parameters
    ----------
    daily_flow_rows:
        Output of :func:`scripts.econ_query_api.load_onchain_daily_flow`.
        A tuple of 585 :class:`OnchainCcopDailyFlow` items spanning
        2024-09-17 → 2026-04-24 (Task 11.A panel).
    friday_anchor_tz:
        IANA timezone name.  Default ``"America/Bogota"`` matches
        Task 11.B convention.  Validated but not otherwise used in this
        date-only aggregation.
    proxy_kind:
        Rev-5.2.1 Task 11.N.1 Step 0 parametrization (RC-new finding).
        ``"net_primary_issuance_usd"`` (the Rev-5.1 default) keeps the
        supply-channel surrogate definition defined above; Rev-5.2.1
        introduces the distribution-channel literal
        ``"b2b_to_b2c_net_flow_usd"`` so this function can tag its
        output with either label under the relaxed
        ``onchain_xd_weekly`` CHECK constraint.  The computation here is
        currently identical for both tags (they share the daily-flow
        input); a full distribution-channel recomputation requires the
        Task 11.N.1 full-transfers panel — callers that need
        edge-level B2B→B2C differential will replace this branch once
        ``onchain_copm_transfers`` rows are landed by the Step-4
        backfill.  In the interim the function honours the ``proxy_kind``
        argument on the resulting :class:`WeeklyXdPanel` so the DuckDB
        ``onchain_xd_weekly`` row tag is set correctly.

    Returns
    -------
    WeeklyXdPanel
        Frozen dataclass with weeks ascending.  ``b2b_addresses`` and
        ``b2c_addresses`` are empty frozensets by default — callers who
        want classifier output should compose
        ``dataclasses.replace(panel, b2b_addresses=..., b2c_addresses=...)``
        after a separate :func:`classify_addresses` call.

    Notes
    -----
    Pure function: reads only its arguments, returns a new dataclass.
    No mutation of input tuples; no global state.
    """
    # Validate the timezone eagerly — ``ZoneInfo`` raises
    # ``ZoneInfoNotFoundError`` on garbage input.
    _ = ZoneInfo(friday_anchor_tz)

    if not daily_flow_rows:
        return WeeklyXdPanel(
            weeks=(),
            values_usd=(),
            is_partial_week=(),
            proxy_kind=proxy_kind,
        )

    # Date-sorted defensive ordering (input from
    # :func:`load_onchain_daily_flow` is already ``ORDER BY date`` but we
    # do not assume it, to preserve input-order-independence).
    sorted_rows: tuple[OnchainCcopDailyFlow, ...] = tuple(
        sorted(daily_flow_rows, key=lambda r: r.date)
    )

    panel_min: date = sorted_rows[0].date
    panel_max: date = sorted_rows[-1].date

    # Bucket daily rows into their Friday-of-ISO-week.  Preserves float
    # precision: we sum float64 USD values whose source is a 6-decimal
    # VARCHAR cast by :func:`load_onchain_daily_flow`.
    bucket_net: dict[date, float] = {}
    for row in sorted_rows:
        friday = _friday_of_iso_week(row.date)
        net = float(row.copm_mint_usd) - float(row.copm_burn_usd)
        bucket_net[friday] = bucket_net.get(friday, 0.0) + net

    # Emit in ascending Friday order.
    fridays: tuple[date, ...] = tuple(sorted(bucket_net.keys()))

    values: list[float] = []
    partials: list[bool] = []
    for friday in fridays:
        values.append(bucket_net[friday])
        monday, sunday = _week_span(friday)
        partial = (monday < panel_min) or (sunday > panel_max)
        partials.append(partial)

    return WeeklyXdPanel(
        weeks=fridays,
        values_usd=tuple(values),
        is_partial_week=tuple(partials),
        proxy_kind=proxy_kind,
    )
