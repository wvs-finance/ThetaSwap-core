# Real A_T Identification — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace equal-share proxy A_T with real per-position fee shares from Dune Collect events, then re-run exit hazard model to get insurance pricing parameter beta_1.

**Architecture:** One Dune query extracts per-position Collect fee amounts. Hardcode results into `data.py`. New `compute_real_daily_at()` function replaces `DAILY_AT_MAP`. All downstream code (hazard model, notebook) unchanged.

**Tech Stack:** Python 3.11, JAX 0.9.1, Dune MCP, uhi8 venv, @functional-python conventions.

---

### Task 0: Run Dune Collect Query via MCP

**Files:**
- Modify: `econometrics/data.py:250-253` (will add RAW_COLLECT_FEES after query returns)

**Step 1: Create the Dune query**

Use the Dune MCP `createDuneQuery` tool to create:

```sql
SELECT
  c.evt_block_time::date AS collect_date,
  c.amount0 / 1e18 AS fee_eth,
  c.amount1 / 1e6 AS fee_usdc,
  b.evt_block_number - m.evt_block_number AS blocklife
FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Collect c
INNER JOIN uniswap_v3_ethereum.UniswapV3Pool_evt_Burn b
  ON c.evt_tx_hash = b.evt_tx_hash
  AND c.contract_address = b.contract_address
  AND c.tickLower = b.tickLower
  AND c.tickUpper = b.tickUpper
INNER JOIN (
  SELECT sender, tickLower, tickUpper, contract_address,
         MAX(evt_block_number) AS evt_block_number
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Mint
  WHERE contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
  GROUP BY sender, tickLower, tickUpper, contract_address
) m
  ON b.owner = m.sender
  AND b.tickLower = m.tickLower
  AND b.tickUpper = m.tickUpper
  AND b.contract_address = m.contract_address
  AND m.evt_block_number < b.evt_block_number
WHERE c.contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
  AND c.evt_block_time >= DATE '2025-12-05'
  AND c.evt_block_time <= DATE '2026-01-14'
  AND (c.amount0 > 0 OR c.amount1 > 0)
ORDER BY c.evt_block_time
```

Name: `theta_swap_collect_fees_q6`

**Step 2: Execute the query**

Use `executeQueryById` with the returned query ID. Wait for results.

**Step 3: Extract results**

Use `getExecutionResults` to fetch the rows. Record the output.

**Step 4: Verify data quality**

Check:
- Row count is approximately 600 (matching RAW_POSITIONS count)
- Date range covers 2025-12-05 to 2026-01-14
- All 41 days have at least 1 Collect event
- blocklife values are > 0

**Note:** If the JOIN on Mint is too expensive or returns wrong matches, fall back to Collect-only (group by collect_date, sum amounts per owner+ticks, compute shares without blocklife — use blocklife from existing RAW_POSITIONS instead).

---

### Task 1: Add CollectFeeRow Type

**Files:**
- Modify: `econometrics/types.py:173` (append after MarginalEffect)
- Test: `tests/econometrics/test_types.py`

**Step 1: Write the failing test**

```python
def test_collect_fee_row_frozen() -> None:
    """CollectFeeRow is a frozen dataclass with correct fields."""
    from econometrics.types import CollectFeeRow
    row = CollectFeeRow(
        collect_date="2025-12-10",
        fee_eth=0.005,
        fee_usdc=15.23,
        blocklife=7200,
    )
    assert row.collect_date == "2025-12-10"
    assert row.fee_eth == 0.005
    assert row.fee_usdc == 15.23
    assert row.blocklife == 7200
```

**Step 2: Run test to verify it fails**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_types.py::test_collect_fee_row_frozen -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

Append to `econometrics/types.py` after the `MarginalEffect` class (line 173):

```python
@dataclass(frozen=True)
class CollectFeeRow:
    """One position's collected fees from Dune Q6 Collect events."""
    collect_date: str
    fee_eth: float
    fee_usdc: float
    blocklife: int
```

**Step 4: Run test to verify it passes**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_types.py::test_collect_fee_row_frozen -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
git add -f econometrics/types.py tests/econometrics/test_types.py
git commit -m "feat(types): add CollectFeeRow for per-position fee data"
```

---

### Task 2: Add RAW_COLLECT_FEES Data + Recompute DAILY_AT_MAP

**Files:**
- Modify: `econometrics/data.py:250-253`
- Modify: `econometrics/ingest.py` (add compute_real_daily_at)
- Test: `tests/econometrics/test_ingest.py`

**Step 1: Write the failing test for compute_real_daily_at**

```python
def test_compute_real_daily_at_basic() -> None:
    """Real A_T uses fee shares, not equal shares."""
    from econometrics.types import CollectFeeRow
    from econometrics.ingest import compute_real_daily_at
    import math

    # Day with 2 positions: one captured 90% of fees, one captured 10%
    rows = [
        CollectFeeRow("2025-12-10", fee_eth=0.0, fee_usdc=90.0, blocklife=100),
        CollectFeeRow("2025-12-10", fee_eth=0.0, fee_usdc=10.0, blocklife=7200),
    ]
    result = compute_real_daily_at(rows)
    assert "2025-12-10" in result

    # x_1 = 90/100 = 0.9, theta_1 = 1/100 = 0.01
    # x_2 = 10/100 = 0.1, theta_2 = 1/7200 ~ 0.000139
    # A_T = sqrt(0.01 * 0.81 + 0.000139 * 0.01) = sqrt(0.008101)
    expected = math.sqrt(0.01 * 0.9**2 + (1.0/7200) * 0.1**2)
    assert abs(result["2025-12-10"] - expected) < 1e-6


def test_compute_real_daily_at_equal_shares() -> None:
    """When fees are equal, real A_T matches equal-share formula."""
    from econometrics.types import CollectFeeRow
    from econometrics.ingest import compute_real_daily_at
    import math

    # 3 positions, equal fees, same blocklife
    rows = [
        CollectFeeRow("2025-12-10", fee_eth=0.0, fee_usdc=100.0, blocklife=7200),
        CollectFeeRow("2025-12-10", fee_eth=0.0, fee_usdc=100.0, blocklife=7200),
        CollectFeeRow("2025-12-10", fee_eth=0.0, fee_usdc=100.0, blocklife=7200),
    ]
    result = compute_real_daily_at(rows)
    # x_k = 1/3 for all, theta_k = 1/7200 for all
    # A_T = sqrt(3 * (1/7200) * (1/3)^2) = sqrt(1/7200 * 1/3) = sqrt(1/21600)
    expected = math.sqrt(3 * (1.0/7200) * (1.0/3)**2)
    assert abs(result["2025-12-10"] - expected) < 1e-6


def test_compute_real_daily_at_multi_day() -> None:
    """Produces one A_T value per day."""
    from econometrics.types import CollectFeeRow
    from econometrics.ingest import compute_real_daily_at

    rows = [
        CollectFeeRow("2025-12-10", fee_eth=0.0, fee_usdc=100.0, blocklife=7200),
        CollectFeeRow("2025-12-10", fee_eth=0.0, fee_usdc=50.0, blocklife=3600),
        CollectFeeRow("2025-12-11", fee_eth=0.0, fee_usdc=200.0, blocklife=1000),
    ]
    result = compute_real_daily_at(rows)
    assert len(result) == 2
    assert "2025-12-10" in result
    assert "2025-12-11" in result
```

**Step 2: Run tests to verify they fail**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_ingest.py::test_compute_real_daily_at_basic tests/econometrics/test_ingest.py::test_compute_real_daily_at_equal_shares tests/econometrics/test_ingest.py::test_compute_real_daily_at_multi_day -v`
Expected: FAIL with ImportError

**Step 3: Implement compute_real_daily_at in ingest.py**

Add import at top of `econometrics/ingest.py`:
```python
from econometrics.types import CollectFeeRow
```

(Add `CollectFeeRow` to the existing import line from `econometrics.types`.)

Add function at end of file:

```python
def compute_real_daily_at(
    collect_data: Sequence[CollectFeeRow],
) -> dict[str, float]:
    """Compute real A_T per day using Eq. 1 from main.pdf.

    A_T = sqrt(sum_k theta_k * x_k^2)
    where x_k = fee_k / sum(fees), theta_k = 1/blocklife_k.

    Uses USDC fees as primary (fee_usdc). Falls back to fee_eth * 3000
    (approximate ETH price) if fee_usdc is zero.
    """
    ETH_PRICE_APPROX: float = 3000.0

    day_groups: dict[str, list[CollectFeeRow]] = {}
    for row in collect_data:
        day_groups.setdefault(row.collect_date, []).append(row)

    result: dict[str, float] = {}
    for day, rows in sorted(day_groups.items()):
        fees = [
            r.fee_usdc + r.fee_eth * ETH_PRICE_APPROX
            for r in rows
            if r.blocklife > 0
        ]
        valid_rows = [r for r in rows if r.blocklife > 0]
        total_fee = sum(fees)
        if total_fee <= 0 or not valid_rows:
            continue

        a_t_squared = sum(
            (1.0 / r.blocklife) * (f / total_fee) ** 2
            for r, f in zip(valid_rows, fees)
        )
        result[day] = math.sqrt(a_t_squared)

    return result
```

**Step 4: Run tests to verify they pass**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_ingest.py::test_compute_real_daily_at_basic tests/econometrics/test_ingest.py::test_compute_real_daily_at_equal_shares tests/econometrics/test_ingest.py::test_compute_real_daily_at_multi_day -v`
Expected: PASS

**Step 5: Add RAW_COLLECT_FEES to data.py and recompute DAILY_AT_MAP**

In `econometrics/data.py`, after `RAW_POSITIONS` (line 249), add:

```python
# ── Q6 per-position Collect fees (from Dune MCP) ──
# Format: (collect_date, fee_eth, fee_usdc, blocklife)
RAW_COLLECT_FEES: Final[list[tuple[str, float, float, int]]] = [
    # PASTE DUNE RESULTS HERE from Task 0
]
```

Replace the DAILY_AT_MAP derivation (lines 251-253):

```python
# ── Daily pool-level A_T: real Eq. 1 from per-position fee shares ──
from econometrics.types import CollectFeeRow as _CFR
from econometrics.ingest import compute_real_daily_at as _compute

_COLLECT_ROWS: Final[list[_CFR]] = [
    _CFR(d, fe, fu, bl) for d, fe, fu, bl in RAW_COLLECT_FEES
]
DAILY_AT_MAP: Final[dict[str, float]] = _compute(_COLLECT_ROWS)
```

**Step 6: Run all existing tests**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/ -v`
Expected: ALL PASS (existing hazard/ingest tests still work because DAILY_AT_MAP interface is unchanged)

**Step 7: Commit**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
git add -f econometrics/data.py econometrics/ingest.py tests/econometrics/test_ingest.py
git commit -m "feat(data): compute real A_T from per-position Collect fees (Eq. 1)"
```

---

### Task 3: Re-run Exit Hazard Notebook

**Files:**
- Read-only: `notebooks/exit_hazard_results.ipynb`

**Step 1: Execute the notebook**

Run:
```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/jupyter nbconvert --to notebook --execute notebooks/exit_hazard_results.ipynb --output exit_hazard_results_executed.ipynb --ExecutePreprocessor.kernel_name=uhi8 --ExecutePreprocessor.timeout=300 2>&1 | tail -20
```

**Step 2: Check results**

Read the executed notebook and extract:
- beta_1 (A_T coefficient) — expected: POSITIVE (sign flip from -4.90)
- cluster_p_value — target: < 0.10
- dose-response monotonicity (Q1 < Q2 < Q3 < Q4 exit rates)
- lag sensitivity (beta_1 > 0 for >= 3 of 5 lags)

**Step 3: Report results**

Print a summary table:

```
| Metric              | Proxy A_T (old) | Real A_T (new) |
|---------------------|-----------------|----------------|
| beta_1              | -4.90           | ???            |
| cluster p-value     | 0.15            | ???            |
| sign                | negative        | ???            |
| dose-response       | ???             | ???            |
```

**Step 4: Clean up**

```bash
rm -f notebooks/exit_hazard_results_executed.ipynb
```

**STOP condition:** If beta_1 is still not positive and significant:
- Report the null result with correct data
- Proceed to fallback: add position-level controls (tickRange, L_i/L_active) per design doc

---

### Task 4: Smoke Test — Full Pipeline End-to-End

**Files:**
- Test: `tests/econometrics/test_hazard.py`

**Step 1: Run full test suite**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/ -v --tb=short`
Expected: ALL PASS

**Step 2: Run the hazard model directly to verify**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -c "
from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS
from econometrics.ingest import build_exit_panel
from econometrics.hazard import logit_mle, marginal_effect_at_means

panel = build_exit_panel(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP, lag_days=1)
result = logit_mle(panel)
print(f'beta_1(A_T) = {result.beta_a_t:.4f}')
print(f'cluster SE  = {result.cluster_se_a_t:.4f}')
print(f'cluster p   = {result.cluster_p_value_a_t:.6f}')
print(f'n_obs       = {result.n_obs}')
print(f'n_exits     = {result.n_exits}')
print(f'n_clusters  = {result.n_clusters}')
print(f'pseudo-R2   = {result.pseudo_r2:.4f}')

me = marginal_effect_at_means(result, delta_a_t=0.10)
print(f'\\nMarginal effect: {me.marginal_effect:.6f}')
print(f'Implied premium: \${me.implied_premium_usd:.2f}')
"
```

**Step 3: Final commit if results are significant**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
git add -f econometrics/ tests/econometrics/
git commit -m "feat(hazard): significant beta_1 with real A_T — insurance demand confirmed"
```
