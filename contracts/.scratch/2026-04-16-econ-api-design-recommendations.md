# Structural Econometrics Query API: Endpoint Design Recommendations

**Date:** 2026-04-16
**Reviewer:** Backend Architect
**Scope:** `contracts/scripts/econ_query_api.py` — pure-function query layer over `structural_econ.duckdb`
**Pattern reference:** `contracts/scripts/ran_data_api.py` (frozen dataclasses, pure free functions, DuckDB conn param)
**Upstream spec:** `contracts/notes/structural-econometrics/specs/2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)

---

## Design Principles

1. **SQL for joins, aggregation, filtering; Python for estimation.** Anything that touches multiple tables or requires window functions belongs in SQL behind the API. Anything that is a statistical operation (OLS, GARCH MLE, hypothesis tests) stays in the notebook.
2. **No lagged-variable pre-computation in SQL.** Lags are trivial in pandas (`df['col'].shift(n)`), and hard-coding lag structure in SQL couples the API to a specific model. Exception: lags already baked into the panel builders (e.g., `oil_return` uses `LAG()` internally) are fine because they define the variable, not the model.
3. **No X/y matrix construction in the API.** Returning a ready-made design matrix couples the API to one specification. The notebook needs the freedom to add/drop regressors, transform LHS, and construct interactions. The API should return clean, named DataFrames.
4. **Frozen dataclasses for metadata; DataFrames for panel data.** Consistent with `ran_data_api.py`.
5. **Every function is conn-first, dates optional with sensible defaults (full sample).**

---

## Review of Proposed Endpoints (7 original)

### 1. `get_weekly_panel(conn, start, end) -> DataFrame`
**Verdict: CORE** — No changes needed. Returns the full weekly panel. Start/end should default to None (full sample).

### 2. `get_daily_panel(conn, start, end) -> DataFrame`
**Verdict: CORE** — Same pattern. Required for GARCH-X estimation (A7/confirmatory co-primary).

### 3. `get_weekly_panel_release_only(conn, start, end) -> DataFrame`
**Verdict: CORE** — Filters `is_cpi_release_week = TRUE OR is_ppi_release_week = TRUE`. Required for T2 (Levene test: release vs non-release variance comparison) and A4 (release-day exclusion). The notebook needs both halves of the split, so consider renaming or pairing (see recommendation 10 below).

### 4. `get_weekly_panel_subsample(conn, start, end, split_date) -> tuple[DataFrame, DataFrame]`
**Verdict: CORE** — Required for A3 (sub-sample splits) and T6 (Chow test). Returning a tuple is correct; the notebook needs both halves.

### 5. `get_manifest(conn) -> list[ManifestRow]`
**Verdict: CORE** — Data provenance. ManifestRow should be a frozen dataclass.

### 6. `get_table_summary(conn) -> dict[str, int]`
**Verdict: CORE** — Quick row counts for all tables. Useful for data validation cells at notebook top.

### 7. `get_rv_excluding_release_day(conn, start, end) -> DataFrame`
**Verdict: CORE** — Required for A4. Must recompute weekly RV from daily_panel excluding rows where `is_cpi_release_day = TRUE` or `is_ppi_release_day = TRUE`. This is a non-trivial SQL aggregation (re-sum squared returns after dropping specific days) that absolutely belongs in the API, not the notebook.

**Implementation note:** This query must join `daily_panel` back to weekly granularity. The SQL should be:
```
SELECT week_start,
       SUM(cop_usd_return * cop_usd_return) AS rv_excl_release,
       POWER(SUM(cop_usd_return * cop_usd_return), 1.0/3.0) AS rv_excl_release_cuberoot,
       COUNT(*) AS n_trading_days_excl
FROM daily_panel
WHERE NOT is_cpi_release_day AND NOT is_ppi_release_day
  AND date BETWEEN ? AND ?
GROUP BY week_start
ORDER BY week_start
```
The notebook then joins this back to the weekly panel for the A4 regression.

---

## Recommended Additional Endpoints

### 8. `get_weekly_panel_by_release_type(conn, start, end) -> tuple[DataFrame, DataFrame, DataFrame]`

**Signature:**
```python
def get_weekly_panel_by_release_type(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (cpi_only_weeks, ppi_only_weeks, both_weeks).

    Splits weekly_panel by release-type flag combinations.
    """
```

**Returns:** Three DataFrames: weeks with only CPI release, weeks with only PPI release, weeks with both CPI and PPI release on the same week.

**Spec requirement:** Co-primary decomposition (section 4.1) needs to separate CPI vs PPI effects. The notebook must know which weeks had which release type to construct the decomposition properly and to check whether CPI and PPI releases overlap (the spec notes DANE releases CPI and PPI on the same day).

**Rating: CORE** — Without this, the notebook author must write boolean logic on `is_cpi_release_week` and `is_ppi_release_week` flags, which is error-prone (the overlap case is easy to miss).

---

### 9. `get_daily_panel_release_days(conn, start, end) -> DataFrame`

**Signature:**
```python
def get_daily_panel_release_days(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return daily_panel rows where is_cpi_release_day OR is_ppi_release_day is TRUE."""
```

**Returns:** DataFrame of daily observations on release days only.

**Spec requirement:** T2 (announcement effect Levene test at daily granularity), GARCH-X variance equation construction (need to identify which days carry the `|s_t^CPI|` exogenous variable in the variance equation).

**Rating: CORE** — The GARCH-X model (confirmatory co-primary) operates on daily data with the surprise variable active only on release days. The notebook must identify these days cleanly.

---

### 10. `get_weekly_panel_release_split(conn, start, end) -> tuple[DataFrame, DataFrame]`

**Signature:**
```python
def get_weekly_panel_release_split(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (release_weeks, non_release_weeks).

    Release = is_cpi_release_week OR is_ppi_release_week.
    """
```

**Returns:** Tuple of (release weeks, non-release weeks).

**Spec requirement:** T2 (Levene test) explicitly requires comparing `Var(RV | release)` vs `Var(RV | non-release)`. The existing `get_weekly_panel_release_only` returns only the release half. The notebook needs both halves without post-filtering.

**Rating: CORE** — Replaces (or supplements) endpoint 3. The Levene test needs BOTH groups. Returning only one group forces the notebook to derive the complement, which is SQL the API should own.

**Decision:** If you keep endpoint 3, add this as a convenience that returns both sides. If you want to minimize API surface, replace endpoint 3 with this one (the release-only half is just `result[0]`).

---

### 11. `get_date_coverage(conn) -> dict[str, DateCoverage]`

**Signature:**
```python
@dataclass(frozen=True)
class DateCoverage:
    table: str
    row_count: int
    date_min: date
    date_max: date
    null_count: int  # NULLs in the primary value column

def get_date_coverage(
    conn: duckdb.DuckDBPyConnection,
) -> dict[str, DateCoverage]:
    """Return date range and row count for every table.

    More detailed than get_table_summary: includes date bounds and NULL counts.
    """
```

**Returns:** Dict mapping table name to a frozen dataclass with row count, min date, max date, and NULL count for the primary value column.

**Spec requirement:** The spec flags three data sources as "UNVERIFIED" (section 4.3). The first notebook cell should validate that all tables have adequate coverage. `get_table_summary` gives only row counts. This adds date bounds and NULL counts, which are the actual validation dimensions.

**Rating: CORE** — The download manifest records expected metadata, but the notebook needs to verify ACTUAL table state. Without date bounds, the notebook cannot confirm the 2003-2026 sample window is covered.

---

### 12. `get_surprise_series(conn, series, start, end) -> DataFrame`

**Signature:**
```python
def get_surprise_series(
    conn: duckdb.DuckDBPyConnection,
    series: Literal['cpi', 'us_cpi', 'ppi'] = 'cpi',
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return the AR(1) surprise series with release dates and raw values.

    Columns: release_date, week_start, raw_pct_change, ar1_surprise, abs_surprise.
    For 'ppi': raw_pct_change is IPP MoM, surprise is standardized deviation from mean.
    """
```

**Returns:** DataFrame with release dates, the raw percentage change, the AR(1) surprise (or standardized PPI change), and absolute surprise. One row per release event.

**Spec requirement:** T1 (consensus rationality F-test on lagged predictors). The notebook must regress `s_t` on `s_{t-1}, RV_{t-1}, VIX_{t-1}` to test that the surprise is unpredictable. This requires the surprise series with its own lags aligned to release dates, not weekly-panel rows (most weeks have zero surprise). The weekly panel embeds the surprise into a 1,215-row frame where 840+ rows are zero; the F-test needs only the ~260 release-event observations.

**Rating: CORE** — The T1 test operates on the surprise series itself, not on the panel. Without this endpoint, the notebook must filter the weekly panel to non-zero surprise rows AND join back to the raw DANE data to get the underlying pct_change. That join logic belongs in the API.

---

### 13. `get_rv_with_lagged(conn, start, end, lags) -> DataFrame`

**Signature:**
```python
def get_rv_with_lagged(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
    lags: int = 1,
) -> pd.DataFrame:
    """Return weekly_panel columns plus rv_lag1, rv_cuberoot_lag1, etc.

    Lags computed via DuckDB LAG() window function on the ordered weekly_panel.
    """
```

**Returns:** Weekly panel augmented with lagged RV columns.

**Spec requirement:** A5 (lagged RV control: add `log(RV_{t-1})` as 6th regressor).

**Rating: SKIP** — Violates design principle 2. `df['rv_cuberoot'].shift(1)` is one line in pandas. Pre-computing lags in SQL couples the API to a specific lag structure. The notebook should do this.

---

### 14. `get_descriptive_stats(conn, start, end) -> DataFrame`

**Signature:**
```python
def get_descriptive_stats(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return summary statistics for all weekly_panel columns.

    Columns: variable, count, mean, std, min, p25, median, p75, max, skewness, kurtosis.
    """
```

**Returns:** One row per variable with standard descriptive statistics including skewness and kurtosis.

**Spec requirement:** T5 (Jarque-Bera normality test requires skewness/kurtosis of residuals, but that is post-estimation). More importantly, every empirical paper's Table 1 is descriptive statistics. The notebook will need this.

**Rating: SKIP** — `df.describe()` plus `df.skew()` and `df.kurtosis()` is three lines of pandas. DuckDB can compute these, but there is no join/filter complexity that justifies SQL. The notebook author will want to customize which variables appear in Table 1 anyway.

---

### 15. `get_correlation_matrix(conn, start, end, columns) -> DataFrame`

**Signature:**
```python
def get_correlation_matrix(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
```

**Returns:** Pairwise correlation matrix for selected weekly_panel columns.

**Spec requirement:** Standard diagnostic; multicollinearity check before OLS.

**Rating: SKIP** — `df[cols].corr()` is one line. No SQL advantage.

---

### 16. `get_intervention_details(conn, start, end) -> DataFrame`

**Signature:**
```python
def get_intervention_details(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return raw intervention data at daily granularity with all 8 type columns.

    Includes week_start mapping for weekly-panel joins.
    """
```

**Returns:** Daily intervention rows with all 8 instrument columns (discretionary, direct_purchase, put_volatility, call_volatility, put_reserve_accum, call_reserve_decum, ndf, fx_swaps) plus week_start assignment.

**Spec requirement:** T7 (intervention control adequacy). The weekly panel collapses intervention into a dummy + total amount. T7 requires comparing beta with/without intervention control, but the notebook might also want to decompose by intervention TYPE (e.g., do FX swaps vs direct purchases have different effects?). The raw data is in `banrep_intervention_daily`, but aligning it to the weekly panel's week_start requires a SQL join.

**Rating: USEFUL** — T7 can be tested with the existing intervention_dummy from the weekly panel (just run two regressions: with/without the column). But if the reviewer or referee asks "which type of intervention drives the control effect?", this endpoint is ready. Not blocking but valuable.

---

### 17. `get_oil_dual_series(conn, start, end) -> DataFrame`

**Signature:**
```python
def get_oil_dual_series(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return weekly oil return AND oil log-level for A8 (oil level control).

    Columns: week_start, oil_return, oil_log_level.
    """
```

**Returns:** Weekly oil data with both return and level.

**Spec requirement:** A8 (oil level control: add `log(P_oil)` as 7th regressor alongside oil return).

**Rating: SKIP** — Both `oil_return` and `oil_log_level` are already columns in the weekly panel. No additional query needed.

---

### 18. `get_subsample_breakpoints(conn) -> list[date]`

**Signature:**
```python
def get_subsample_breakpoints(
    conn: duckdb.DuckDBPyConnection,
) -> list[date]:
    """Return canonical sub-sample split dates from the spec.

    Returns [date(2015,1,5), date(2021,1,4)] for the three periods:
    2003-2014, 2015-2020, 2021-2025.
    """
```

**Returns:** List of Monday dates that define the sub-sample boundaries.

**Spec requirement:** A3 (sub-sample splits: 2003-14, 2015-20, 2021-25) and T6 (Chow test).

**Rating: SKIP** — These are constants from the spec, not data-derived. They belong in a config dataclass or module-level constant, not in a query function. The notebook can define them as:
```python
SPLIT_DATES = [date(2015, 1, 5), date(2021, 1, 4)]
```

---

### 19. `get_asymmetric_surprise_panel(conn, start, end) -> DataFrame`

**Signature:**
```python
def get_asymmetric_surprise_panel(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return weekly panel augmented with s_plus and s_minus columns.

    s_plus = max(cpi_surprise_ar1, 0)
    s_minus = min(cpi_surprise_ar1, 0)
    """
```

**Returns:** Weekly panel with two additional columns for asymmetric surprise decomposition.

**Spec requirement:** A9 (asymmetric effects: split surprise into positive and negative components).

**Rating: SKIP** — Two lines in pandas:
```python
df['s_plus'] = df['cpi_surprise_ar1'].clip(lower=0)
df['s_minus'] = df['cpi_surprise_ar1'].clip(upper=0)
```
No SQL advantage. The transformation is trivially invertible and the notebook author will understand it better inline.

---

### 20. `get_release_calendar_aligned(conn, series, start, end) -> DataFrame`

**Signature:**
```python
def get_release_calendar_aligned(
    conn: duckdb.DuckDBPyConnection,
    series: Literal['ipc', 'ipp', 'bls'] = 'ipc',
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return release calendar with week_start alignment and actual values.

    For 'ipc': joins dane_release_calendar to dane_ipc_monthly.
    For 'ipp': joins dane_release_calendar to dane_ipp_monthly.
    For 'bls': joins bls_release_calendar to fred_monthly (CPIAUCSL).
    Columns: year, month, release_date, week_start, actual_value, pct_change, imputed.
    """
```

**Returns:** Release calendar with the actual data values joined in and week_start computed.

**Spec requirement:** Multiple. The release calendar is the backbone of the surprise construction. The notebook needs it for: (a) verifying AR(1) surprise alignment, (b) identifying which months had imputed release dates, (c) constructing event-study windows, (d) the CUSUM plot (plotting cumulative surprise over time against release dates).

**Rating: CORE** — The join between release calendars and actual data values is a three-table operation (calendar + monthly data + week_start computation). This is exactly the kind of SQL the API should own. Without it, the notebook author must replicate the join logic from `econ_panels.py`.

---

### 21. `get_monthly_panel(conn, start, end) -> DataFrame`

**Signature:**
```python
def get_monthly_panel(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return monthly-frequency panel for A1 (monthly horizon sensitivity).

    Aggregates daily returns to monthly RV. Joins monthly CPI/PPI, VIX average,
    oil return, intervention count, US CPI.
    Columns: month_start, rv_monthly, rv_monthly_cuberoot, rv_monthly_log,
             n_trading_days, dane_ipc_pct, dane_ipp_pct, us_cpi_surprise,
             cpi_surprise_ar1, vix_avg, oil_return, intervention_dummy,
             intervention_amount, banrep_rate_surprise.
    """
```

**Returns:** Monthly-frequency analogue of the weekly panel.

**Spec requirement:** A1 (monthly horizon: LHS = log(monthly RV), N ~ 260). This is a completely different aggregation level. The weekly panel cannot be trivially summed to monthly because (a) months do not align to weeks, (b) monthly RV must be computed from daily returns within calendar months, not from weekly RVs, (c) control variable alignment changes.

**Rating: CORE** — This is a significant SQL aggregation (monthly grouping of daily returns, re-joining controls at monthly frequency). Building this in the notebook would mean writing 50+ lines of pandas groupby logic that duplicates the panel-builder pattern. The SQL is better: DuckDB handles the date arithmetic and joins efficiently.

---

### 22. `get_standardized_ppi_change(conn, start, end) -> DataFrame`

**Signature:**
```python
def get_standardized_ppi_change(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return standardized PPI change series for co-primary decomposition.

    Computes (IPP_pct - mean(IPP_pct)) / std(IPP_pct) using expanding window.
    Columns: release_date, week_start, raw_ipp_pct, standardized_ipp_change.
    """
```

**Returns:** PPI change standardized to same scale as CPI surprise, aligned to release weeks.

**Spec requirement:** Co-primary decomposition (section 4.1): "standardized PPI change: mean-subtracted and sigma-divided, same scale as CPI surprise, so beta_1 and beta_2 both measure vol response per 1-SD shock and are directly comparable." The spec explicitly requires expanding-window standardization (not full-sample, to avoid look-ahead).

**Rating: CORE** — The expanding-window standardization is the same pattern as the AR(1) surprise in `compute_ar1_surprises()`. It must be computed carefully to avoid look-ahead bias. This logic belongs in the API (or panel builder) because: (a) it requires an expanding window (not trivial in pandas without a loop), (b) the result must align to release weeks via the calendar join, and (c) getting it wrong introduces look-ahead bias that invalidates the decomposition. The AR(1) surprise builder in `econ_panels.py` already demonstrates the pattern.

---

### 23. `get_panel_completeness(conn) -> DataFrame`

**Signature:**
```python
def get_panel_completeness(
    conn: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Return per-column NULL/zero counts for weekly_panel and daily_panel.

    Columns: panel, column_name, total_rows, null_count, zero_count, pct_populated.
    """
```

**Returns:** Data quality summary for both panels.

**Spec requirement:** Not directly tied to a spec test, but the panels have several columns initialized to 0.0 (us_cpi_surprise, cpi_surprise_ar1, banrep_rate_surprise) that are only populated by `compute_ar1_surprises()`. If the pipeline ran partially, some columns may still be all-zero. The notebook must verify this before estimation.

**Rating: CORE** — A zero-valued surprise column that should have data is a silent bug that produces a zero beta, not an error. The notebook needs a fast way to detect this. The SQL is a multi-column aggregation across both panels that is tedious to write in pandas.

---

## Summary Table

| # | Function | Rating | Serves |
|---|---|---|---|
| 1 | `get_weekly_panel` | CORE | Primary OLS, all sensitivities |
| 2 | `get_daily_panel` | CORE | GARCH-X (A7/confirmatory) |
| 3 | `get_weekly_panel_release_only` | CORE (see 10) | T2, A4 |
| 4 | `get_weekly_panel_subsample` | CORE | A3, T6 |
| 5 | `get_manifest` | CORE | Data provenance |
| 6 | `get_table_summary` | CORE | Validation |
| 7 | `get_rv_excluding_release_day` | CORE | A4 |
| 8 | `get_weekly_panel_by_release_type` | **CORE (NEW)** | Co-primary decomposition |
| 9 | `get_daily_panel_release_days` | **CORE (NEW)** | GARCH-X, T2 daily |
| 10 | `get_weekly_panel_release_split` | **CORE (NEW)** | T2 Levene test |
| 11 | `get_date_coverage` | **CORE (NEW)** | Data validation |
| 12 | `get_surprise_series` | **CORE (NEW)** | T1 rationality test |
| 13 | `get_rv_with_lagged` | SKIP | A5 (trivial in pandas) |
| 14 | `get_descriptive_stats` | SKIP | Table 1 (trivial in pandas) |
| 15 | `get_correlation_matrix` | SKIP | Diagnostics (trivial in pandas) |
| 16 | `get_intervention_details` | **USEFUL (NEW)** | T7 deep-dive |
| 17 | `get_oil_dual_series` | SKIP | A8 (already in weekly panel) |
| 18 | `get_subsample_breakpoints` | SKIP | A3 (constants, not a query) |
| 19 | `get_asymmetric_surprise_panel` | SKIP | A9 (trivial in pandas) |
| 20 | `get_release_calendar_aligned` | **CORE (NEW)** | Surprise verification, CUSUM |
| 21 | `get_monthly_panel` | **CORE (NEW)** | A1 (monthly horizon) |
| 22 | `get_standardized_ppi_change` | **CORE (NEW)** | Co-primary decomposition |
| 23 | `get_panel_completeness` | **CORE (NEW)** | Data quality gate |

**Final count:** 7 original + 9 CORE new + 1 USEFUL new = 17 endpoints total (6 SKIP).

---

## Additional Design Recommendations

### A. Domain Types Module

Define a small set of frozen dataclasses for non-DataFrame returns:

```python
@dataclass(frozen=True)
class ManifestRow:
    source: str
    downloaded_at: datetime
    row_count: int | None
    date_min: date | None
    date_max: date | None
    sha256: str | None
    url_or_path: str | None
    status: str
    notes: str | None

@dataclass(frozen=True)
class DateCoverage:
    table: str
    row_count: int
    date_min: date | None
    date_max: date | None
    null_count: int
```

### B. Error Handling

Follow `ran_data_api.py` pattern: define a `QueryError` exception. Raise it when:
- A requested table does not exist (panel not yet built)
- The date range yields zero rows
- A required column is all-NULL (panel builder ran but surprise computation did not)

Do NOT raise on empty surprise series (some series legitimately have no releases in a given range). Return empty DataFrame with correct column schema instead.

### C. Connection Management

The API should NOT own the connection. Every function takes `conn` as first argument. The notebook opens the connection once:
```python
conn = duckdb.connect("contracts/data/structural_econ.duckdb", read_only=True)
```
This matches `ran_data_api.py` and keeps the API pure.

### D. Constants to Export

The API module should export (as module-level `Final` constants) the column lists that define the pre-committed specification:

```python
PRIMARY_LHS: Final[str] = "rv_cuberoot"
PRIMARY_RHS: Final[tuple[str, ...]] = (
    "cpi_surprise_ar1",
    "us_cpi_surprise",
    "banrep_rate_surprise",
    "vix_avg",
    "intervention_dummy",
    "oil_return",
)
```

This way the notebook can reference `econ_query_api.PRIMARY_RHS` instead of hard-coding column names. If the spec changes, the API is the single source of truth.

### E. What the Notebook Still Owns

The API deliberately does NOT cover:
- OLS estimation (statsmodels)
- GARCH-X MLE (arch package)
- Newey-West HAC computation
- Hypothesis tests (F-test, Levene, Ljung-Box, Jarque-Bera, Chow)
- CUSUM computation
- Plotting
- Lagged variable construction
- Asymmetric surprise decomposition (clip operations)
- Descriptive statistics and correlation matrices

These are all estimation-layer concerns. The API is the data-access layer. Mixing them would violate separation of concerns and make the API untestable without statistical packages as dependencies.
