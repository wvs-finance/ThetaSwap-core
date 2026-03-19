# ThetaSwap Research

Empirical research supporting the Fee Concentration Index -- a quadratic deviation exit hazard model for adverse competition risk in concentrated liquidity AMMs.

We study 3,365 position-day observations from the ETH/USDC 30bps pool on Uniswap V3 (41 days, 600 positions, 597 exit events). The analysis establishes an inverted-U relationship between fee share deviation and exit hazard, with a turning point at delta\* ~ 0.09 and demand identification via a 2.65x real-vs-null A\_T ratio. The full narrative is in [narrative/problem.md](./narrative/problem.md) (problem statement) and [narrative/research-summary.md](./narrative/research-summary.md) (three-pillar summary with all coefficients and backtest results).

---

## Econometrics

Duration and hazard models estimating how fee concentration deviation drives LP exit rates.

| Module | Description |
|--------|-------------|
| [econometrics/types.py](./econometrics/types.py) | Data structures for positions, durations, and hazard records |
| [econometrics/data.py](./econometrics/data.py) | Data loading and transformation pipelines |
| [econometrics/ingest.py](./econometrics/ingest.py) | Uniswap V3 event ingestion from Dune/subgraph sources |
| [econometrics/hazard.py](./econometrics/hazard.py) | Quadratic deviation exit hazard model implementation |
| [econometrics/duration.py](./econometrics/duration.py) | Duration analysis for position lifetimes |
| [econometrics/estimate.py](./econometrics/estimate.py) | Logistic regression estimation with clustered standard errors |
| [econometrics/per_position_data.py](./econometrics/per_position_data.py) | Per-position metric computation (fee shares, IL, age) |
| [econometrics/run_duration.py](./econometrics/run_duration.py) | CLI entry point for duration analysis |
| [econometrics/cross_pool/](./econometrics/cross_pool/) | Cross-pool concentration severity analysis (subgraph data, multi-pool comparison) |

**Notebook:** [notebooks/eth-usdc-insurance-demand-identification.ipynb](./notebooks/eth-usdc-insurance-demand-identification.ipynb) -- full econometric identification pipeline with regression tables and dose-response curves.

<details>
<summary>Key Equations</summary>

**Fee Concentration Accumulator (A\_T)**

$$A_T = \left(\sum_{k} \theta_k \cdot x_k^2\right)^{1/2}$$

where $x_k$ is the fee share captured by position $k$ and $\theta_k = 1/\Delta B_k$ is the sophistication weight (inverse lifetime in blocks).

**Concentration Deviation**

$$\Delta^+ = \max(0,\; A_T - A_T^{1/N})$$

where $A_T^{1/N}$ is the Ma-Crapis competitive null (equal fee shares).

**Turning Point**

$$\delta^* = \frac{-\hat{\beta}_1}{2\hat{\beta}_2} \approx 0.09$$

Below $\delta^*$, concentration is protective (shelter regime). Above it, concentration drives LP exits (Capponi regime).

</details>

---

## Backtest

Insurance backtest engine simulating trigger-based and threshold-based insurance payoffs against historical data.

| Module | Description |
|--------|-------------|
| [backtest/daily.py](./backtest/daily.py) | Daily position tracking and panel construction |
| [backtest/sweep.py](./backtest/sweep.py) | Parameter sweep for trigger calibration |
| [backtest/calibrate.py](./backtest/calibrate.py) | Model calibration (gamma, seed capital, reserve dynamics) |
| [backtest/payoff.py](./backtest/payoff.py) | Insurance payoff computation (p-squared and alternatives) |
| [backtest/plotting.py](./backtest/plotting.py) | Publication-quality figure generation (300 DPI) |
| [backtest/pnl.py](./backtest/pnl.py) | PnL and hedge value computation per position |
| [backtest/types.py](./backtest/types.py) | Data structures for backtest records and results |
| [backtest/mechanism_sweep.py](./backtest/mechanism_sweep.py) | Multi-mechanism comparison sweep (trigger vs. exit-based) |
| [backtest/oracle_comparison.py](./backtest/oracle_comparison.py) | Oracle accumulation method comparison |
| [backtest/synthetic_exits.py](./backtest/synthetic_exits.py) | Synthetic exit generation for stress testing |

**Notebook:** [notebooks/eth-usdc-backtest.ipynb](./notebooks/eth-usdc-backtest.ipynb) -- full backtest pipeline with payoff comparison tables and reserve dynamics.

<details>
<summary>Key Equations</summary>

**Concentration Deviation (DeltaPlus)**

$$\Delta^+ = \max(0,\; 1 - A_T)$$

**p-Squared Insurance Payoff**

$$\text{payout} = \gamma \cdot \text{lifetime\_fees} \times \left[\left(\frac{p_{\max}}{p^*}\right)^2 - 1\right]^+$$

where $p_{\max}$ is the maximum concentration price experienced during the position's lifetime, $p^* = \delta^*/(1 - \delta^*)$ is the strike price derived from the econometric turning point, and $\gamma = 3.30\%$ is the calibrated base premium factor.

</details>

---

## Model

LaTeX mathematical specification of the FCI mechanism, payoff structure, and econometric methodology.

| File | Description |
|------|-------------|
| [model/main.tex](./model/main.tex) | Master document (inputs all sections) |
| [model/main.pdf](./model/main.pdf) | Compiled specification |
| [model/payoff.tex](./model/payoff.tex) | FCI definition, co-primary state variables, price mapping |
| [model/econometrics.tex](./model/econometrics.tex) | Full econometric specification with regression tables |
| [model/trading-function.tex](./model/trading-function.tex) | CFMM trading function specification |
| [model/reserves.tex](./model/reserves.tex) | Reserve dynamics and funding |
| [model/borrow-rate.tex](./model/borrow-rate.tex) | Borrow rate model |
| [model/preamble.tex](./model/preamble.tex) | LaTeX preamble (packages, macros) |

---

## Data

Cached Dune query results, frozen fixtures for reproducible fork tests, and oracle scripts.

| Directory | Description |
|-----------|-------------|
| [data/fixtures/](./data/fixtures/) | Frozen datasets for Forge fork tests (loaded via `vm.readFile`) |
| [data/queries/](./data/queries/) | Dune SQL queries and subgraph queries |
| [data/scripts/](./data/scripts/) | FFI oracle scripts -- [fci_oracle.py](./data/scripts/fci_oracle.py), [fci_epoch_oracle.py](./data/scripts/fci_epoch_oracle.py), [verify_provenance.py](./data/scripts/verify_provenance.py) |
| [data/econometrics/](./data/econometrics/) | Serialized estimation results (duration, lagged regression JSONs) |
| [data/frozen/](./data/frozen/) | Frozen intermediate artifacts |

**Data provenance:** All empirical data was extracted and verified using the [Dune MCP](https://github.com/duneanalytics/dune-mcp-server) integration. The SQL queries in [data/queries/dune/](./data/queries/dune/) are executable on Dune Analytics and reproduce the datasets used throughout this research. See [data/queries/README.md](./data/queries/README.md) for query IDs, reproduction costs, and the full data flow diagram.

---

## Figures

Publication-style plots generated from Phase 1 notebooks (300 DPI).

| File | Description |
|------|-------------|
| [figures/alpha-sweep.png](./figures/alpha-sweep.png) | Payoff exponent sweep comparing alpha = 1, 2, 3 |
| [figures/dose-response.png](./figures/dose-response.png) | Dose-response curve showing inverted-U exit hazard |
| [figures/reserve-dynamics.png](./figures/reserve-dynamics.png) | Insurance reserve evolution over observation window |
| [figures/trigger-days.png](./figures/trigger-days.png) | Trigger day identification (delta > delta\*) |

---

## Notebooks

| Notebook | Description |
|----------|-------------|
| [notebooks/eth-usdc-insurance-demand-identification.ipynb](./notebooks/eth-usdc-insurance-demand-identification.ipynb) | Econometric identification: regression tables, dose-response, signal decay |
| [notebooks/eth-usdc-backtest.ipynb](./notebooks/eth-usdc-backtest.ipynb) | Insurance backtest: payoff comparison, reserve dynamics, calibration |
| [notebooks/cross-pool-concentration-severity.ipynb](./notebooks/cross-pool-concentration-severity.ipynb) | Cross-pool concentration severity analysis |
| [notebooks/duration_results.ipynb](./notebooks/duration_results.ipynb) | Duration model results and diagnostics |
| [notebooks/oracle-accumulation-comparison.ipynb](./notebooks/oracle-accumulation-comparison.ipynb) | Oracle accumulation method comparison |

---

## Tests

Python test suite covering econometrics, backtest, and data modules.

```bash
PYTHONPATH=research pytest research/tests -v
```

Test subdirectories: [tests/econometrics/](./tests/econometrics/), [tests/backtest/](./tests/backtest/), [tests/data/](./tests/data/), plus [tests/test_simulator.py](./tests/test_simulator.py).
