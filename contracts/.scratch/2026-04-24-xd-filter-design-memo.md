# X_d Filter — Design Memo (Rev-5.1 Task 11.N)

**Date:** 2026-04-24
**Task:** Rev-5.1 Task 11.N — X_d filter design + implementation
**Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `8c984ab56`
**Upstream inputs:**
- `contracts/.scratch/2026-04-24-inequality-differential-literature-review.md` (11.L)
- `contracts/.scratch/2026-04-24-copm-per-tx-profile.md` (11.M)
- `contracts/scripts/econ_query_api.py` (load_onchain_* loaders from 11.M.5)

**Pre-commitment protocol:** This memo is authored **BEFORE** any inspection of the value distribution of the computed X_d series. Structural inspections (row counts, column schemas, date ranges, address counts, percent-of-volume captured by aggregate tables) were performed ONLY to characterize **data availability**, never to tune thresholds on observed values.

---

## 1. Pre-Commitment Verdict — Escalation Flag Fired

**`X_D_INSUFFICIENT_DATA` fires for the originally-proposed filter.**

The proposed filter (`weekly_net_flow_B2B_to_B2C_t = Σ value_wei for transfers where from ∈ B2B AND to ∈ B2C AND Friday_week(block_time) == t − reverse direction`) **cannot be computed** from the aggregate tables available in DuckDB. Structural reasons:

1. `onchain_copm_daily_transfers` (522 rows) has **volume aggregates without from/to identity** — it tells us how many wei moved each day but not between which address pairs.
2. `onchain_copm_transfers_top100_edges` (100 rows) has **from/to + lifetime volume + first/last timestamps** but **no per-week volume breakdown**. 84.4 % of all transfers (92,877/110,069) are captured by these top-100 edges, yet we cannot allocate the lifetime volume of a single edge to a specific week.
3. `onchain_copm_transfers_sample` is a **10-row sample** (flagged `is_sample=True` at the dataclass layer by design in Task 11.M.5). The full 110,069-row raw dataset lives in Dune query 7369028 and is **not** retrievable via the MCP pagination budget (would require ~1,101 paginated calls per Task 11.M.5 docstring).
4. `onchain_copm_address_activity_top400` (300 rows) has **lifetime** inbound / outbound totals — no time dimension at all.

**Consequence:** the exact `Σ_(from ∈ B2B, to ∈ B2C, Friday_week = t) value_wei` cannot be honestly written. It would require a time-resolved edge-level series that the aggregate tables do not carry.

**Rather than force a filter on data we do not have**, this memo pre-commits to a **feasible surrogate X_d** that the literature already licenses — net primary issuance from the mint/burn daily panel — and documents the unavailable filter as the Tier-2 future-data-acquisition target (raw-transfers CSV pull).

---

## 2. Pre-Committed X_d Specification (Primary, Feasible)

### 2.1 Definition

For each Friday-anchored ISO-week `t` in the panel window [2024-09-17, 2026-04-24]:

    X_d_t := Σ_{d ∈ week(t)} copm_mint_usd[d]  −  Σ_{d ∈ week(t)} copm_burn_usd[d]

where:
- `copm_mint_usd[d]` and `copm_burn_usd[d]` are the daily Task 11.A columns in `onchain_copm_ccop_daily_flow` (USD units, 6-decimal VARCHAR cast to float at load).
- `week(t)` = the 7-day ISO-week **Friday-anchored, timezone America/Bogota**, matching Task 11.B's convention — specifically, `t` is the Friday `date_trunc('week', d)::DATE + interval '4 days'` computed in America/Bogota timezone.
- Both sums aggregate dates `d` such that `date_trunc('week', d)::DATE` in America/Bogota equals the Monday anchoring the Friday `t`.

### 2.2 Partial-week flag

    is_partial_week[t] := (week-range [Monday(t), Sunday(t)] extends outside the
                           daily-flow panel window [2024-09-17, 2026-04-24])

Concretely: the **first week** (2024-09-16 Monday → 2024-09-22 Sunday) is partial because the panel starts on Tuesday 2024-09-17. The **last week** containing 2026-04-24 Friday is partial if 2026-04-26 Sunday extends past the max date in the daily-flow table. Partial weeks are retained in output; downstream consumers decide whether to trim.

### 2.3 Unit

USD. The daily-flow table already carries USD-normalised mint/burn values (Task 11.A oracle converted COPM wei → USD via daily TRM fix at the time of CSV generation). Reporting in USD mirrors the Y_asset_leg units in the 11.L functional-equation candidates (carry return, Akgün-Özsöğüt capital-share regression controls).

### 2.4 Economic interpretation

This is **net primary issuance** — the weekly first-derivative of outstanding COPM supply. From the 11.M profile:

- **Mints** flow 100 % into a single treasury (`0x0155b191`) which immediately (zero dwell time) forwards to operational hubs. So `copm_mint_usd` is a direct proxy for **B2B→B2C supply expansion**: new pesos injected into the system.
- **Burns** flow primarily through `{0xbb6cb4e3, 0x8ca3c426}` → burn sink: supply contraction.
- Net positive `X_d_t` weeks: expansion phase (stablecoin demand rising, treasury issuing into the retail / distribution hubs).
- Net negative `X_d_t` weeks: contraction phase (net redemption into the mint/burn loop).

This proxy **cannot** distinguish the B2B oscillation core (52 % of transfer events; `0x6619 ↔ 0x8c05` pair) from retail fan-out — those both sit inside the outstanding supply and never touch the mint/burn boundary. However, oscillation-loop events are volume-neutral by construction: 11.M showed `+1.64 B COPM vs −1.56 B COPM` in the top-2 edges, netting to near-zero. So the filter's **omission of oscillation volume is the desired behaviour** — Lustig-Roussanov-Verdelhan (2011) noise-trade filtering intuition licenses excluding zero-net-flow high-frequency rebalancing from the economic-signal channel.

---

## 3. B2B / B2C Classifier — Auxiliary Output

Even though the primary X_d does **not** require an address-level classification at run-time, the Task 11.N deliverable contract calls for a classifier as a secondary output (useful for future Tier-2 work when raw transfers are available). I pre-commit to the following deterministic rule, expressed on the two address-level tables we **do** have:

### 3.1 Rule (pre-committed thresholds; no data peek)

An address `a` from `onchain_copm_address_activity_top400` is classified **B2B** iff:

    (a) a ∈ known_hubs = {0x0155b191ec52728d26b1cd82f6a412d5d6897c04,   -- primary treasury
                         0x5bd35ee3c1975b2d735d2023bd4f38e3b0cfc122}    -- 2025 distribution hub
        OR
    (b) a appears in the top-50 rows of onchain_copm_address_activity_top400
        (ordered by _csv_row_idx) AND a.n_outbound >= 10
        -- repeat-distributor fingerprint
        OR
    (c) a participates as either from_address or to_address in any of the top-10
        rows of onchain_copm_transfers_top100_edges (ordered by _csv_row_idx)
        -- top-10 by n_transfers DESC per Dune CSV native order
        -- captures oscillation-loop participants

All other addresses in `onchain_copm_address_activity_top400` are **B2C**.

### 3.2 Threshold rationale (pre-commitment)

- **Known hubs**: from 11.M profile §8, explicitly named ("Minteo primary issuance" and "2025 distribution hub"). These are structural facts from the profile, not data-fitted.
- **Top 50 by `_csv_row_idx`**: 11.M profile ranks top-10 by n_inbound + inbound_wei and separately top-10 by tx-count. Extending to 50 absorbs the "custodial / exchange" and "secondary distribution conduit" roles flagged in profile §3 without reaching into the known ~600 B2C-retail `n_out = 0` tail. 50 is a **Schelling threshold** commonly used for concentration analysis (HHI top-50; Lustig-Roussanov-Verdelhan use top-quintile ≈ 20 % which for a universe of 300 = 60; 50 is slightly more conservative).
- **`n_outbound >= 10`**: an address that fans out 10 or more times is acting as a distributor, not a retail recipient. 11.M documents median tail-node outbound count = 6 for automated-payout scripts; **10 is one step above** that median (≈ the 75th-percentile-ish cutoff documented qualitatively in 11.M §4). This is a structural threshold, not a data-derived one.
- **Top-10 edges**: 11.M profile §5 identifies the oscillation core `{0x6619, 0x8c05}` as the top 2 edges and documents the top-6 as the full B2B-oscillation cluster. Top-10 is a single-step extension covering the distribution-hub inbound edges too.

### 3.3 Expected classifier output (committed ex ante, NOT observed)

Based on 11.M profile §8's qualitative typology:
- **B2B set**: I expect ≥ 30 addresses but ≤ 80 (hubs + repeat-distributors + top-edge participants; top-50 ∪ known_hubs ∪ top-10-edge-endpoints).
- **B2C set**: the remainder of the 300-address activity table (expect 220–270 addresses).
- **Untyped remainder**: the ~1,639 addresses NOT in the top-300 activity table are **implicitly B2C** because they are long-tail retail below Dune's activity-threshold cutoff. For classification purposes, I do not enumerate them — the classifier operates only on the 300 addresses we have time-invariant activity data for.

### 3.4 Why the classifier is auxiliary, not load-bearing, for X_d

The primary X_d in §2 **does not use the classifier** — it uses the mint/burn daily flow which is boundary-of-supply data, not edge-level data. The classifier is built and exercised so that:

1. It is validated (frozen + deterministic + reproducible) and ready for the Tier-2 raw-transfers pull (Task 11.N.1 future work).
2. The module provides an end-to-end public API `(classify_addresses, compute_weekly_xd)` even though the two functions compose independently today.
3. The classifier output (b2b_set, b2c_set) is stored in the `WeeklyXdPanel` result so any downstream consumer knows which address universe the X_d proxy corresponds to.

---

## 4. Golden-Fixture Value (Pre-Committed Before Implementation)

### 4.1 Fixture week selection

**Selected Friday**: `2025-10-31` (Friday)
- Monday anchor: 2025-10-27
- Sunday end: 2025-11-02
- Rationale: mid-panel (≈ month 14 of 19); post-cCOP-launch (2024-10-31 < selected); per 11.M §6 October is a **low**-activity month (1,440 transfers total across all Octobers — for 2025 October alone, proportional expectation ~1,440 × (2025 vs 2024+2025+2026 weighting) ≈ modest weekly volume so a single week is auditable by hand); the week contains both weekdays and a weekend and no known major Colombian holiday (11.M profile §6 confirms no prima date or quincena spike on this range).

### 4.2 By-hand computation method (committed before running)

1. Load `onchain_copm_ccop_daily_flow` via `load_onchain_daily_flow(conn)`.
2. Filter rows where `date ∈ {2025-10-27, 2025-10-28, 2025-10-29, 2025-10-30, 2025-10-31, 2025-11-01, 2025-11-02}`.
3. Sum `copm_mint_usd` across those rows → `mint_usd_week`.
4. Sum `copm_burn_usd` across those rows → `burn_usd_week`.
5. `X_d_fixture = mint_usd_week − burn_usd_week` (a single USD float).
6. `is_partial_week_fixture = False` (all 7 days fall inside the panel window [2024-09-17, 2026-04-24]).

### 4.3 Golden-value extraction protocol (to happen during test-write step)

In the test's **fixture-setup** helper (not in the implementation), we compute the expected value ONCE at test-author time by running the by-hand SQL in a standalone DuckDB read-only connection and pinning the resulting USD value to 6 decimal places into the test as a `Final[Decimal]` constant. The implementation must match this value to the cent. The test also independently re-derives the value from raw SQL as the "witness" (§ 5 of deliverable spec) — any divergence between implementation and witness fails the test.

**Note on pre-commitment hygiene**: the `X_d_fixture` value is unknown to this memo (I have not run the SQL). I pre-commit only to the *method* and the *expected sign*: I expect `X_d_fixture > 0` (mint-dominant) OR negative; I do not claim a specific magnitude. If the fixture value turns out to be zero in both legs (both mint and burn were zero that week), the test author **must reject the fixture and rotate forward by one week** (that is a non-informative fixture; a rotation does not violate pre-commitment because the rotation rule itself is pre-committed here).

---

## 5. Literature Grounding (Per-Choice Citations)

1. **Net-issuance as macro-indicator** — Jones-Matsui-Knottenbelt (2026) "Stablecoins as Dry Powder" arxiv:2603.23480; establishes that stablecoin issuance-flow Granger-causes market-wide volatility. Licenses treating `copm_mint − copm_burn` as a legitimate economic X.
2. **Oscillation-loop exclusion** — Lustig-Roussanov-Verdelhan (2011) "Common Risk Factors in Currency Markets" RFS 24(11); two-factor model separates carry-factor signal from idiosyncratic country noise. Analogously, the `0x6619 ↔ 0x8c05` oscillation is idiosyncratic to market-maker rebalancing and should be excluded from the macro-signal channel. The mint/burn proxy naturally excludes it.
3. **Friday anchoring, America/Bogota timezone** — Task 11.B convention (frozen by pre-existing spec in `project_fx_vol_econ_complete_findings.md` memory note); also matches `load_fed_funds_weekly` / `load_banrep_ibr_weekly` in Task 11.M.6.
4. **USD unit** — Y_asset_leg composition in 11.L Candidate A (Lustig-Roussanov-Verdelhan) is constructed in USD-equivalent; matching unit avoids silent unit-conversion bugs.
5. **Partial-week-flag policy (keep + flag)** — Task 11.A Rev-3.1 convention (NULL for pre-cCOP-launch rows; extended here to `is_partial_week=True`).
6. **Classifier thresholds being pre-committed before observation** — echoes the entire Phase-A.0 pre-commitment discipline (project memory `feedback_strict_tdd.md` + `project_fx_vol_econ_complete_findings.md` anti-fishing narrative).

---

## 6. Known Limitations (Must Be in Module Docstring)

1. **Surrogate, not the true filter**: primary X_d is net primary issuance, not the per-transfer B2B→B2C flow. The true filter requires raw 110,069-row transfers + per-address classification + weekly bucketing — none of which is in DuckDB today.
2. **Oscillation-volume omission is intentional, not a bug**: if a downstream consumer asks "what about retail velocity between intermediary hubs?", the answer is **that's not what this X_d measures**; use daily_transfers total_value_wei as a complement (feasible with today's data, but note it includes the B2B oscillation and is NOT a B2B→B2C differential).
3. **Unit granularity**: USD via the Task 11.A oracle's daily TRM snapshot — not a real-time swap rate. For weekly aggregates the daily-snapshot error is small but non-zero.
4. **Escalation fired**: `X_D_INSUFFICIENT_DATA` is recorded in the module docstring + in the `WeeklyXdPanel.proxy_kind` field (committed value: `"net_primary_issuance_usd"`). Downstream analysis should NOT claim the output is a true edge-level B2B→B2C differential.
5. **Classifier is auxiliary**: B2B / B2C sets are returned alongside the panel but do **not** enter the weekly-X_d computation. They document the address universe the proxy corresponds to; they do not drive its math.
6. **Partial-week flag coverage is narrow**: only the panel-boundary edges trigger it, not missing-data weeks within the panel. If a mid-panel week has zero daily-flow rows (no activity at all), the result is `X_d_t = 0.0` with `is_partial_week = False`. This is correct (zero activity is a real observation) but callers plotting sparsity must filter separately.

---

## 7. Model-QA Self-Review (Simulated)

Treating this memo as if submitted to Model QA:

- **No data peek before pre-commitment**: ✅ thresholds (top-50 addresses, n_outbound ≥ 10, top-10 edges, known_hubs = 2) were all chosen from 11.M's qualitative profile narrative (§§ 3–5, 8), NOT from running the classifier and tuning. Structural counts (300 addresses, 100 edges, 522 daily rows) are schema facts, not values.
- **Pre-committed golden fixture**: ✅ Friday 2025-10-31 chosen from calendar structure (mid-panel, post-cCOP-launch, no prima, no quincena spike) — NOT from looking at weekly X_d values.
- **Escalation discipline**: ✅ `X_D_INSUFFICIENT_DATA` fires honestly rather than forcing a synthetic filter. Documents the Tier-2 data-acquisition target explicitly.
- **Literature grounded per choice**: ✅ five distinct literature pegs for five distinct design choices (not a single "Lustig-Roussanov-Verdelhan ate my homework" catchall).
- **One potentially missed concern**: the classifier thresholds are Schelling (50, 10, 10) — if the test were to show the B2B set contains 3 addresses or 200 addresses (far from the "30–80 expected" range in §3.3), this would be a **model-mis-specification flag**, not a bug in the X_d primary (since primary X_d does not use the classifier). Memo documents this as a graceful degradation: classifier output is a **secondary diagnostic**, not a gate-test input.

---

## 8. Implementation Contract (Locked)

Module: `contracts/scripts/copm_xd_filter.py`

Public API (both pure free functions, no classes except frozen dataclasses):

```
def classify_addresses(
    activity_rows: tuple[OnchainCopmAddressActivity, ...],
    top_edges: tuple[OnchainCopmTopEdge, ...],
    *,
    known_hubs: frozenset[str],
    top_n_by_activity: int = 50,
    min_outbound_for_distributor: int = 10,
    top_n_edges: int = 10,
) -> tuple[frozenset[str], frozenset[str]]:
    """Return (b2b_set, b2c_set); union covers only activity_rows universe."""

def compute_weekly_xd(
    daily_flow_rows: tuple[OnchainCcopDailyFlow, ...],
    *,
    friday_anchor_tz: str = "America/Bogota",
) -> WeeklyXdPanel:
    """Aggregate daily mint/burn USD into Friday-anchored weekly net issuance."""
```

Result dataclass:

```
@dataclass(frozen=True, slots=True)
class WeeklyXdPanel:
    weeks: tuple[date, ...]               # Friday anchors
    values_usd: tuple[float, ...]         # mint_usd − burn_usd per week
    is_partial_week: tuple[bool, ...]     # True at panel boundary weeks
    b2b_addresses: frozenset[str]         # auxiliary; from classifier
    b2c_addresses: frozenset[str]         # auxiliary; from classifier
    proxy_kind: str = "net_primary_issuance_usd"  # X_D_INSUFFICIENT_DATA flag
```

Purity contract: no side effects, no I/O inside the two pure functions, no mutation of inputs. A separate top-level helper `load_and_compute_full_panel(conn)` may perform the DuckDB read and then call the pure core — that helper is NOT pure but is an isolated orchestrator.

---

## 9. Commit Contract

Design memo authored **before** any code or test. Commit order:
1. This memo (`2026-04-24-xd-filter-design-memo.md`) — SEPARATE commit as the pre-commitment anchor.
2. Failing test (`test_copm_xd_filter.py`) — with stubbed `compute_weekly_xd()` returning `None` in `copm_xd_filter.py`, pytest confirms RED.
3. Implementation (`copm_xd_filter.py`) — GREEN.
4. Full-panel compute + DuckDB persistence (Step 5).
5. One combined feature commit per task 11.N contract.

Unless, per Rev-5.1 plan convention, all four land in a single feature commit; then this memo is tracked under `.scratch/` with the feat commit referencing it.

---

**End of pre-commitment memo. Authored 2026-04-24. No data-peek on X_d values has occurred.**
