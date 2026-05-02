# Pair D Stage-2 Path B — Phase 0 Task 0.2 — Python deps + DuckDB + Polars + pyarrow version pin

**Author:** Data Engineer dispatch (Phase 0 scaffolding)
**Run timestamp UTC:** 2026-05-02T22:05Z
**Venv path:** `contracts/.venv` (Python 3.13.5)
**Install method:** `uv pip install` (per `feedback_venv_activation`; `source contracts/.venv/bin/activate` precedes any forge --ffi or pytest in this worktree)

## §1 — Pinned versions (live `uv pip list` output, post-install)

| package | version | role in Path B |
|---|---|---|
| `duckdb` | `1.5.1` | local analytical SQL substrate per spec §5; reads / writes Parquet directly; backs `audit_summary.parquet`, `address_inventory.parquet`, `event_inventory.parquet` per §4.0 schema |
| `polars` | `1.40.1` | Polars DataFrame for v0/v1/v2 panel construction; preferred over pandas for memory-efficient on-chain row windowing |
| `polars-runtime-32` | `1.40.1` | Polars CPU runtime variant (32-bit-precision SIMD baseline); auto-installed by polars wheel selector |
| `pyarrow` | `24.0.0` | Snappy-compressed Parquet read / write engine per §4.0; schema_version metadata field hashing |
| `requests` | `2.32.5` | HTTPS client for SQD Network gateway, Alchemy free, Dune, public RPC fallback (per §5 + §5.A) |
| `tomli` | `2.4.1` | TOML parser for `network_config.toml` (Python 3.13.5 pre-stdlib `tomllib` exists as `import tomllib` — `tomli` retained as 3.10 fallback for forward portability) |
| `pandas` | `3.0.2` | inherited from Pair D Stage-1; bridges DuckDB ↔ Parquet ↔ statsmodels OLS in the v3 backtest |
| `numpy` | `2.4.2` | inherited; vector ops underlying the v3 P&L envelope |
| `statsmodels` | `0.14.6` | OLS + HAC SE per FLAG-B1 estimator; required by v1 `r_(a_l)` regression (Newey-West kernel) |
| `sympy` | `1.14.0` | symbolic verification of FLAG-B1 algebra in notebook 02 trio C citation block |
| `matplotlib` | `3.10.8` | qualitative shape-check chart per Task 2.4 |
| `jupyter` | `1.1.1` | `jupyter` meta-package for notebook execution |
| `jupyterlab` | `4.5.6` | local notebook IDE (developer-side) |
| `nbconvert` | `7.17.1` | headless `nbconvert --execute` integration test per `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons` 5-instance silent-test-pass guard |
| `nbformat` | `5.10.4` | notebook JSON validation in scaffolding |
| `ipykernel` | `7.2.0` | kernel registration |
| `jinja2` | `3.1.6` | nbconvert template substitution + auto-rendered README pattern from Stage-1 Pair D |

## §2 — Verification protocol

```text
$ source contracts/.venv/bin/activate
$ python -c "import duckdb, polars, pyarrow, requests, tomli, statsmodels, pandas, numpy"
# (succeeds; no output)

$ python -c "
import duckdb, polars as pl
df = pl.DataFrame({'a': [1, 2, 3], 'b': [10.0, 20.0, 30.0]})
con = duckdb.connect(':memory:')
result = con.execute('SELECT a, b, a*b AS c FROM df').pl()
assert result.shape == (3, 3), 'roundtrip failed'
print('repl roundtrip duckdb<->polars: OK')
"
repl roundtrip duckdb<->polars: OK
```

REPL roundtrip confirms DuckDB 1.5.1 ↔ Polars 1.40.1 cross-compat for the v0/v1 panel substrate.

## §3 — Free-tier compliance

All listed packages are open-source, MIT/BSD/Apache-2 licensed, install from PyPI public index. Zero paid dependencies. Spec §5 free-tier pin upheld.

## §4 — Lockfile pointer

This Phase 0 deps install does NOT modify any committed `requirements.txt` / `pyproject.toml` in the worktree. The Path B notebook directory at `contracts/notebooks/pair_d_stage_2_path_b/` will inherit the venv-pinned versions; if a future committed lockfile is required, the values pinned in §1 above are the source of truth.

## §5 — Rate-limiter implementation note (forward-pointing for Phase 1+)

The `requests` library will be wrapped in a thin sequential-issuance harness (≥250 ms inter-call sleep for SQD Network; ≤25-receipt window × ≥1 s sleep for Alchemy receipt enrichment per spec §5.A burst-rate analysis). Concurrency cap = 1 per source. The `req_per_sec` + `cu_per_sec` audit log writes to `contracts/.scratch/path-b-stage-2/phase-0/burst_rate_log.csv` (header-only at Phase 0; first rows land in Phase 1 Task 1.2 per-venue audit). No async / threading is required at Phase 0; Phase 1+ keeps the same constraint.

## §6 — Next task pointer

Task 0.3 — Network config (`network_config.toml`) + burst-rate harness CSV + DATA_PROVENANCE template.
