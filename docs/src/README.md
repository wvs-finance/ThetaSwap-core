# ThetaSwap Core

Fee concentration insurance protocol for Uniswap V4 passive LPs.

## Prerequisites

- [Foundry](https://book.getfoundry.sh/getting-started/installation) (forge, cast, anvil)
- Python >= 3.11

## Quick Start

```bash
# Clone with submodules
git clone --recurse-submodules <repo-url>
cd thetaSwap-core-dev

# One-command setup (venv + deps + Jupyter kernel)
make install

# Run all tests
make test
```

## Solidity (Fee Concentration Index)

```bash
forge build          # compile contracts
forge test           # run Solidity tests
forge test -vvv      # verbose output
```

Contracts live in `src/fee-concentration-index/`. Tests in `test/fee-concentration-index/`.

## Python (Econometrics + Backtest)

```bash
# Activate venv
source .venv/bin/activate

# Run Python tests
make test-py
# or directly:
PYTHONPATH=research pytest research/tests -v

# Execute all notebooks headless
make notebooks
```

Research code lives in `research/`:
- `research/econometrics/` — hazard model, duration model, ingestion
- `research/backtest/` — insurance backtest engine
- `research/data/` — cached Dune query results
- `research/notebooks/` — reproducible result notebooks
- `research/tests/` — Python test suite

### Manual Python Setup (without Make)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# For notebooks: register a Jupyter kernel
python -m ipykernel install --user --name=thetaswap \
    --env PYTHONPATH "$(pwd)/research"
```

### Running Notebooks

Notebooks expect a kernel with `PYTHONPATH` pointing to `research/`. The `make install` command sets this up automatically. To run interactively:

```bash
source .venv/bin/activate
jupyter lab --notebook-dir=research/notebooks
```

Select the **thetaswap** kernel when opening notebooks.

## Project Structure

```
src/fee-concentration-index/   Solidity hook contract
test/fee-concentration-index/  Solidity tests (Foundry)
research/
  econometrics/                Hazard + duration models
  backtest/                    Insurance backtest engine
  data/                        Cached Dune query data
  notebooks/                   Result notebooks (4)
  tests/                       Python tests (pytest)
specs/                         LaTeX specs + econometric model
docs/plans/                    Implementation plans
lib/                           Foundry dependencies (submodules)
```
