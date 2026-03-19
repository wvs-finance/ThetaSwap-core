# Fee Concentration Duration Model — Design

## Goal

Implement the structural econometric specification from `specs/econometrics/lp-insurance-demand.tex`: does fee concentration risk (A_T) shorten LP position lifetimes? Prove insurance demand for ThetaSwap.

## Architecture

Five components: data extraction, types, lagged treatment, HC1 duration model with sensitivity sweeps, and one display notebook. All computation in Python modules (@functional-python), display-only notebook (uhi8 kernel). Zero new Dune queries — all data already collected.

## Data

- **Daily A_T**: 41 days (2025-12-05 to 2026-01-14), extracted from Q4v2 burn-date A_T values
- **IL proxy**: 41 days from Q5
- **Positions**: 600 rows from Q4v2 (burn_date, blocklife, exit-day A_T)
- **Limitation**: Positions minted before 2025-12-05 lack pre-window A_T. Excluded from lagged-max analysis if mint_date < earliest A_T date.

## Components

### 1. `econometrics/data.py` — Hardcoded Data

Extract `RAW_POSITIONS`, `DAILY_AT_MAP`, `IL_MAP` from `run_duration.py` into standalone module. Single source of truth.

### 2. `econometrics/types.py` — Updated Types

- `LaggedPositionRow(burn_date, blocklife, max_a_t, mean_a_t, median_a_t, il_proxy, mint_date_approx)`
- `RobustDurationResult` — adds `robust_se_a_t`, `robust_p_value_a_t` to existing fields
- `SensitivityRow(lag, measure, beta_a_t, se_a_t, p_value_a_t, n_obs)`
- `QuartileRow(quartile, mean_blocklife, mean_a_t, n_obs)`

### 3. `econometrics/ingest.py` — Lagged Treatment

- `approximate_mint_date(burn_date, blocklife) -> str`: convert blocklife to days, subtract from burn_date
- `compute_lagged_treatment(daily_at_map, mint_date, burn_date, lag_days) -> tuple[float, float, float]`: returns (max, mean, median) A_T over [mint_date, burn_date - lag]
- `build_lagged_positions(raw_positions, daily_at_map, il_map, lag_days) -> list[LaggedPositionRow]`

### 4. `econometrics/duration.py` — Model + Tests

- `duration_model_robust(positions) -> RobustDurationResult`: OLS + HC1 robust SEs
- `sensitivity_sweep(raw_positions, daily_at_map, il_map, lags, measures) -> list[SensitivityRow]`
- `quartile_analysis(positions) -> list[QuartileRow]`
- `nested_models(positions) -> dict[str, RobustDurationResult]`: full vs A_T-only vs IL-only
- `economic_magnitude(result, delta_a_t=0.10) -> dict`: hours shortened, factor, implied value

### 5. `notebooks/duration_results.ipynb` — Display Only

uhi8 kernel. Cells:
1. Import + run main model
2. Main result table
3. Economic magnitude
4. Dose-response quartile chart (matplotlib)
5. Lag sensitivity table/heatmap
6. Nested model comparison table
7. Implied insurance value

## Constraints

- `.gitignore` has `*.py` rule — use `git add -f` for all Python files
- JAX 0.9.1 CPU in uhi8 venv
- @functional-python: frozen dataclasses, free pure functions, full typing, no inheritance
- All data hardcoded (no Dune MCP calls at runtime)
- Notebook is display-only (no computation in cells beyond function calls)

## Testing

- `pytest` tests for each module in `tests/econometrics/`
- Test lagged treatment computation with known data
- Test HC1 SEs against manual calculation
- Test sensitivity sweep produces expected shape
