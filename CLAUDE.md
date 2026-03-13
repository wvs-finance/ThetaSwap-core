# thetaSwap-core-dev Development Guidelines

Last updated: 2026-03-07

## Active Technologies
- Solidity ^0.8.26 + Uniswap V4 core (PoolManager, Hooks, StateLibrary, TickBitmap), forge-std, kontrol-cheatcodes, Solady (FixedPointMathLib), MasterHook diamond (hook-bazaar/monorepo), Compose extensions
- Diamond storage pattern (keccak256 slot hashing, disjoint slots per facet)
- Python 3.11+ (research: backtest, econometrics, oracle)

## Project Structure

```text
src/                          # Solidity contracts
test/                         # Forge tests (unit, fuzz, fork)
specs/                        # Contract specifications (per-feature: specs/001-*/, specs/002-*/)
script/                       # Forge deployment scripts
docs/plans/                   # Branch-specific plans and designs (see rules below)
research/                     # All research/analysis artifacts
  backtest/                   #   Insurance backtest pipeline (8 modules)
  econometrics/               #   Duration, hazard, cross-pool analysis (13 modules)
  data/                       #   Fixtures, raw events, queries, oracle scripts
  model/                      #   LaTeX spec + main.pdf
  notebooks/                  #   Jupyter notebooks (4)
  scripts/                    #   FFI oracles
  tests/                      #   Python tests (114)
skills/                       # Claude skill definitions
app/                          # Frontend app (design-os, committed as regular files — NOT a submodule)
```

## Frontend App (`app/`)

The `app/` directory contains a copy of [buildermethods/design-os](https://github.com/buildermethods/design-os) (Vite + React). It is committed as regular files in the monorepo (not a git submodule).

### IMPORTANT: Project Documentation Context
When working inside `app/`, you MUST read project documentation from the parent monorepo at `../` (relative to `app/`). This includes:
- `../specs/` — contract specifications
- `../research/` — research artifacts (backtest, econometrics, model, notebooks)
- `../docs/plans/` — branch-specific plans
- `../CLAUDE.md` — project guidelines

The app consumes and displays data from the core protocol. Always reference the parent project's specs and research when building UI features.

## Branch Rules (ENFORCED)

### Rule 1: Branch-scoped plans
Each branch owns ONLY its plans in `docs/plans/`. Plans MUST relate to the branch's feature:
- `001-fee-concentration-index` → plans about FCI contract, fork tests, index math
- `002-theta-swap-cfmm` → plans about CFMM trading function, price representation, reserves
- `003-reactive-integration` → plans about reactive network adapter, V3 event integration

When creating plans, name them `docs/plans/YYYY-MM-DD-<topic>.md`. Do NOT create plans for other branches' features.

### Rule 2: Shared research state
`research/` MUST be identical across all feature branches (001, 002, 003). After modifying anything under `research/`:
1. Commit and push on the current branch
2. Cherry-pick or checkout the `research/` dir to the other two branches
3. Verify with: `git diff origin/001-fee-concentration-index origin/002-theta-swap-cfmm -- research/ | wc -l` (must be 0)

The `.gitignore` file must also stay in sync across branches.

## Commands

```bash
# Forge tests
forge test --match-path "test/fee-concentration-index/**" -vv

# Python tests
make test-py
# or: PYTHONPATH=research pytest research/tests -v

# Oracle
uhi8/bin/python research/data/scripts/fci_oracle.py

# Notebooks (execute headless)
make notebooks

# Verify branch sync
git diff origin/001-fee-concentration-index origin/002-theta-swap-cfmm -- research/ | wc -l
```

## Code Style

- Solidity ^0.8.26: Follow standard conventions, no `is` inheritance in production contracts
- Python: Frozen dataclasses, free pure functions, full typing (per @functional-python skill)

## Recent Changes
- 003-reactive-integration: Reactive hook adapter, V3 event integration, merged 001 FCI dependency
- 002-theta-swap-cfmm: Diamond storage, MasterHook, Compose extensions
- 001-fee-concentration-index: FCI contract, partial-remove guard, dead code removal, DX setup

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
