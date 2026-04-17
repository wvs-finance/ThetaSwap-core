default:
    @just --list

ci: check-format check-clippy test test-integration

check: check-format check-clippy test

fix: fix-format fix-clippy

test:
    cargo nextest run --workspace --lib

test-integration:
    cargo nextest run --workspace --tests

check-format:
    cargo +nightly fmt --all -- --check

fix-format:
    cargo +nightly fmt --all

check-clippy:
    cargo clippy --all-targets -- -D warnings

fix-clippy:
    cargo clippy --all-targets --fix --allow-dirty --allow-staged

build:
    cargo build --release

clean:
    cargo clean

# Execute and export the FX-vol CPI-surprise / Colombia notebooks headlessly.
#
# Scope-expansion rationale (plan Rule 4): Phase 0 econ-notebook tasks are
# otherwise contained to contracts/ (scripts/, notebooks/, data/, .gitignore).
# The `notebooks:` recipe below is the ONE user-approved exception — it lives
# at the worktree root because `just` resolves recipes relative to the
# justfile directory and we want `just notebooks` callable from anywhere in
# the repo. See:
#   contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md
#   (Non-Negotiable Rule 4, Task 1d)
#
# Two phases, fail-fast ordering:
#   1. `--execute --to notebook --inplace` runs NB1 → NB2 → NB3 in order.
#      Timeout is pinned to 1800s (matches env.NBCONVERT_TIMEOUT); NB3's
#      bootstrap + specification-curve fits can exceed the 600s default.
#   2. `--to pdf` exports each notebook. Only runs if every execute step
#      succeeded — just aborts on the first non-zero exit.
notebooks:
    cd contracts && .venv/bin/jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb
    cd contracts && .venv/bin/jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/fx_vol_cpi_surprise/Colombia/02_estimation.ipynb
    cd contracts && .venv/bin/jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/fx_vol_cpi_surprise/Colombia/03_tests_and_sensitivity.ipynb
    cd contracts && .venv/bin/jupyter nbconvert --to pdf notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb
    cd contracts && .venv/bin/jupyter nbconvert --to pdf notebooks/fx_vol_cpi_surprise/Colombia/02_estimation.ipynb
    cd contracts && .venv/bin/jupyter nbconvert --to pdf notebooks/fx_vol_cpi_surprise/Colombia/03_tests_and_sensitivity.ipynb

# Install the pre-commit hook in .git/hooks/pre-commit.
#
# Run ONCE per clone (per worktree). Required to gate commits on
# contracts/scripts/lint_notebook_citations.py (Task 5 — Rule 6
# citation-block + Rule 7 chasing-offline lint for FX-vol notebooks).
#
# The worktree's .git is a pointer file (sub-worktree layout); pre-commit
# handles this internally and installs the hook into the correct
# .git/modules/<path>/hooks/ location in the main repo.
#
# Closes the trapdoor flagged in the review: without this step, a new
# contributor's commits bypass the notebook citation lint silently.
pre-commit-install:
    cd contracts && .venv/bin/pre-commit install

