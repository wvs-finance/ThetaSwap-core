# LP Insurance Demand — Data Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract Uniswap V3 ETH/USDC 30bps event data via BigQuery MCP, classify JIT positions, compute A_T, and produce a regression-ready panel dataset for the structural logit estimation.

**Architecture:** BigQuery MCP handles extraction and heavy SQL aggregation. Python (@functional-python) handles A_T computation, panel assembly, and structural logit estimation. Data flows: BigQuery → JSON → Parquet → pandas → statsmodels. JIT classification is same-transaction mint+burn (discovered in Tier 1 exploration).

**Tech Stack:** BigQuery MCP (mcp__bigquery__execute-query), Python 3.14 (uhi8 venv), pandas, pyarrow, numpy, scipy, statsmodels. All Python code uses frozen dataclasses, free pure functions, full typing per @functional-python.

**Venv:** `source /home/jmsbpp/apps/ThetaSwap/ThetaSwap-research/uhi8/bin/activate`

**Working directory:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/`

**Key constants:**
- Pool: ETH/USDC 30bps `0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8`
- Block range: 21350000–22000000 (~3 months, Tier 1 validated)
- Mint topic: `0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde`
- Burn topic: `0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c`
- Swap topic: `0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67`

**Upstream spec:** `specs/econometrics/lp-insurance-demand.tex`

**Tier 1 results (already validated):**
- 2,070 Mints, 2,875 Burns in 3-month window
- 166 JIT transactions (same-tx mint+burn)
- Lagged corr(JIT_{t-1}, passive_burns_t) = +0.40

**Event layouts (from BigQuery exploration):**

Mint: topics = [sig, owner(indexed), tickLower(indexed), tickUpper(indexed)], data = [sender(address), amount(uint128), amount0(uint256), amount1(uint256)]

Burn: topics = [sig, owner(indexed), tickLower(indexed), tickUpper(indexed)], data = [amount(uint128), amount0(uint256), amount1(uint256)]

Swap: topics = [sig, sender(indexed), recipient(indexed)], data = [amount0(int256), amount1(int256), sqrtPriceX96(uint160), liquidity(uint128), tick(int24)]

---

## Task 0: Environment Setup

**Files:**
- Create: `econometrics/__init__.py`
- Create: `econometrics/types.py`
- Create: `data/econometrics/.gitkeep`

**Step 1: Install dependencies into uhi8 venv**

```bash
source /home/jmsbpp/apps/ThetaSwap/ThetaSwap-research/uhi8/bin/activate
pip install pyarrow db-dtypes
```

Verify:
```bash
python -c "import pyarrow; print('pyarrow', pyarrow.__version__)"
```
Expected: `pyarrow X.Y.Z`

**Step 2: Create package and domain types**

```python
# econometrics/__init__.py
"""LP insurance demand econometric pipeline."""
```

```python
# econometrics/types.py
"""Domain types — frozen dataclasses, type aliases, constants per @functional-python."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypeAlias

# ── Constants ──────────────────────────────────────────────────────────
POOL_ADDRESS: Final = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
POOL_NAME: Final = "ETH/USDC 30bps"
FEE_TIER: Final = 3000

MINT_TOPIC: Final = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
BURN_TOPIC: Final = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
SWAP_TOPIC: Final = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"

START_BLOCK: Final = 21_350_000
END_BLOCK: Final = 22_000_000

BLOCKS_PER_DAY: Final = 7_200
MIN_JIT_EVENTS: Final = 50

DATA_DIR: Final = "data/econometrics"
PARQUET_DIR: Final = "data/econometrics/parquet"


# ── Type Aliases ───────────────────────────────────────────────────────
HexStr: TypeAlias = str
Address: TypeAlias = str
BlockNumber: TypeAlias = int


# ── Value Types ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class MintEvent:
    """Decoded Uniswap V3 Mint event."""
    block_number: BlockNumber
    tx_hash: HexStr
    log_index: int
    owner: Address
    tick_lower: int
    tick_upper: int
    sender: Address
    amount: int
    amount0: int
    amount1: int


@dataclass(frozen=True)
class BurnEvent:
    """Decoded Uniswap V3 Burn event."""
    block_number: BlockNumber
    tx_hash: HexStr
    log_index: int
    owner: Address
    tick_lower: int
    tick_upper: int
    amount: int
    amount0: int
    amount1: int


@dataclass(frozen=True)
class SwapEvent:
    """Decoded Uniswap V3 Swap event."""
    block_number: BlockNumber
    tx_hash: HexStr
    log_index: int
    sender: Address
    recipient: Address
    amount0: int
    amount1: int
    sqrt_price_x96: int
    liquidity: int
    tick: int


@dataclass(frozen=True)
class PositionLifecycle:
    """A completed position lifecycle (mint → burn)."""
    owner: Address
    tick_lower: int
    tick_upper: int
    amount: int
    mint_block: BlockNumber
    burn_block: BlockNumber
    mint_tx: HexStr
    burn_tx: HexStr
    blocklife: int
    is_jit: bool
    theta: float  # sophistication weight = 1/blocklife


@dataclass(frozen=True)
class PanelRow:
    """One row of the estimation panel."""
    owner: Address
    block: BlockNumber
    exit: int  # 1 = burn (exit)
    a_t: float
    blocklife: int
    tick_lower: int
    tick_upper: int
    amount: int
    jit_count_lag1: int  # JIT events in prior day (instrument)
    swap_count: int  # swap volume proxy (control)
```

**Step 3: Create data directory**

```bash
mkdir -p data/econometrics/parquet
touch data/econometrics/.gitkeep
```

**Step 4: Commit**

```bash
git add econometrics/__init__.py econometrics/types.py data/econometrics/.gitkeep
git commit -m "feat(econometrics): domain types and constants"
```

---

## Task 1: Event Decoding — Pure Functions

**Files:**
- Create: `econometrics/decode.py`
- Create: `tests/econometrics/__init__.py`
- Create: `tests/econometrics/test_decode.py`

**Step 1: Write the failing test**

```python
# tests/econometrics/__init__.py
# (empty)

# tests/econometrics/test_decode.py
"""Tests for event log decoding."""
from econometrics.decode import decode_mint, decode_burn, hex_to_int, hex_to_address
from econometrics.types import MintEvent, BurnEvent


def test_hex_to_address_extracts_last_20_bytes() -> None:
    raw = "0x000000000000000000000000c36442b4a4522e871399cd717abdd847ab11fe88"
    assert hex_to_address(raw) == "0xc36442b4a4522e871399cd717abdd847ab11fe88"


def test_hex_to_int_unsigned() -> None:
    assert hex_to_int("0x0000000000000000000000000000000000000000000000000000000000030084") == 196740


def test_hex_to_int_signed_negative() -> None:
    raw = "0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc4898"
    result = hex_to_int(raw, signed=True)
    assert result < 0


def test_decode_mint_from_real_log() -> None:
    """Decode a real Mint log from ETH/USDC 30bps pool."""
    topics = [
        "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde",
        "0x000000000000000000000000c36442b4a4522e871399cd717abdd847ab11fe88",
        "0x000000000000000000000000000000000000000000000000000000000002ffd0",
        "0x00000000000000000000000000000000000000000000000000000000000308f4",
    ]
    data = (
        "0x"
        "000000000000000000000000c36442b4a4522e871399cd717abdd847ab11fe88"
        "000000000000000000000000000000000000000000000000000011eae5bde4f9"
        "0000000000000000000000000000000000000000000000000000000005f5e100"
        "0000000000000000000000000000000000000000000000000de0b6b3a7640000"
    )
    result = decode_mint(topics, data, block_number=21927131, tx_hash="0xabc", log_index=40)
    assert isinstance(result, MintEvent)
    assert result.owner == "0xc36442b4a4522e871399cd717abdd847ab11fe88"
    assert result.tick_lower == 196560  # 0x2ffd0
    assert result.tick_upper == 198900  # 0x308f4
    assert result.amount > 0
    assert result.block_number == 21927131


def test_decode_burn_from_real_log() -> None:
    """Decode a real Burn log from ETH/USDC 30bps pool."""
    topics = [
        "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c",
        "0x0000000000000000000000001f2f10d1c40777ae1da742455c65828ff36df387",
        "0x00000000000000000000000000000000000000000000000000000000000302dc",
        "0x0000000000000000000000000000000000000000000000000000000000030318",
    ]
    data = (
        "0x"
        "00000000000000000000000000000000000000000000000082330cff00000000"
        "0000000000000000000000000000000000000000000000000000005f768051cc"
        "0000000000000000000000000000000000000000000000000de0b6b3a7640000"
    )
    result = decode_burn(topics, data, block_number=21898492, tx_hash="0xdef", log_index=51)
    assert isinstance(result, BurnEvent)
    assert result.owner == "0x1f2f10d1c40777ae1da742455c65828ff36df387"
    assert result.tick_lower == 197340  # 0x302dc
    assert result.tick_upper == 197400  # 0x30318
```

**Step 2: Run test to verify failure**

```bash
source /home/jmsbpp/apps/ThetaSwap/ThetaSwap-research/uhi8/bin/activate
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
python -m pytest tests/econometrics/test_decode.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'econometrics.decode'`

**Step 3: Implement decoding — free pure functions**

```python
# econometrics/decode.py
"""Pure functions for decoding Uniswap V3 event logs."""
from __future__ import annotations

from typing import Sequence

from econometrics.types import (
    MintEvent, BurnEvent, SwapEvent,
    HexStr, Address, BlockNumber,
)


def hex_to_int(hex_str: HexStr, signed: bool = False) -> int:
    """Convert hex string to integer, handling sign extension."""
    value = int(hex_str, 16)
    if signed and value >= (1 << 255):
        value -= 1 << 256
    return value


def hex_to_address(hex_str: HexStr) -> Address:
    """Extract address from 32-byte hex-encoded topic."""
    return "0x" + hex_str[-40:].lower()


def _data_words(data: HexStr) -> list[str]:
    """Split data hex string into 32-byte words."""
    raw = data[2:] if data.startswith("0x") else data
    return [raw[i:i + 64] for i in range(0, len(raw), 64)]


def decode_mint(
    topics: Sequence[HexStr],
    data: HexStr,
    block_number: BlockNumber,
    tx_hash: HexStr,
    log_index: int,
) -> MintEvent:
    """Decode Uniswap V3 Mint event.

    Mint(address sender, address indexed owner,
         int24 indexed tickLower, int24 indexed tickUpper,
         uint128 amount, uint256 amount0, uint256 amount1)

    topics: [sig, owner, tickLower, tickUpper]
    data: [sender, amount, amount0, amount1]
    """
    owner = hex_to_address(topics[1])
    tick_lower = hex_to_int(topics[2], signed=True)
    tick_upper = hex_to_int(topics[3], signed=True)

    words = _data_words(data)
    sender = hex_to_address("0x" + words[0])
    amount = hex_to_int("0x" + words[1])
    amount0 = hex_to_int("0x" + words[2])
    amount1 = hex_to_int("0x" + words[3])

    return MintEvent(
        block_number=block_number, tx_hash=tx_hash, log_index=log_index,
        owner=owner, tick_lower=tick_lower, tick_upper=tick_upper,
        sender=sender, amount=amount, amount0=amount0, amount1=amount1,
    )


def decode_burn(
    topics: Sequence[HexStr],
    data: HexStr,
    block_number: BlockNumber,
    tx_hash: HexStr,
    log_index: int,
) -> BurnEvent:
    """Decode Uniswap V3 Burn event.

    Burn(address indexed owner, int24 indexed tickLower,
         int24 indexed tickUpper, uint128 amount,
         uint256 amount0, uint256 amount1)

    topics: [sig, owner, tickLower, tickUpper]
    data: [amount, amount0, amount1]
    """
    owner = hex_to_address(topics[1])
    tick_lower = hex_to_int(topics[2], signed=True)
    tick_upper = hex_to_int(topics[3], signed=True)

    words = _data_words(data)
    amount = hex_to_int("0x" + words[0])
    amount0 = hex_to_int("0x" + words[1])
    amount1 = hex_to_int("0x" + words[2])

    return BurnEvent(
        block_number=block_number, tx_hash=tx_hash, log_index=log_index,
        owner=owner, tick_lower=tick_lower, tick_upper=tick_upper,
        amount=amount, amount0=amount0, amount1=amount1,
    )


def decode_swap(
    topics: Sequence[HexStr],
    data: HexStr,
    block_number: BlockNumber,
    tx_hash: HexStr,
    log_index: int,
) -> SwapEvent:
    """Decode Uniswap V3 Swap event.

    Swap(address indexed sender, address indexed recipient,
         int256 amount0, int256 amount1, uint160 sqrtPriceX96,
         uint128 liquidity, int24 tick)

    topics: [sig, sender, recipient]
    data: [amount0, amount1, sqrtPriceX96, liquidity, tick]
    """
    sender = hex_to_address(topics[1])
    recipient = hex_to_address(topics[2])

    words = _data_words(data)
    amount0 = hex_to_int("0x" + words[0], signed=True)
    amount1 = hex_to_int("0x" + words[1], signed=True)
    sqrt_price_x96 = hex_to_int("0x" + words[2])
    liquidity = hex_to_int("0x" + words[3])
    tick = hex_to_int("0x" + words[4], signed=True)

    return SwapEvent(
        block_number=block_number, tx_hash=tx_hash, log_index=log_index,
        sender=sender, recipient=recipient,
        amount0=amount0, amount1=amount1, sqrt_price_x96=sqrt_price_x96,
        liquidity=liquidity, tick=tick,
    )
```

**Step 4: Run tests**

```bash
python -m pytest tests/econometrics/test_decode.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add econometrics/decode.py tests/econometrics/
git commit -m "feat(econometrics): pure event log decoders for V3 Mint/Burn/Swap"
```

---

## Task 2: BigQuery Extraction to Parquet

**Files:**
- Create: `econometrics/extract.py`

This task uses the BigQuery MCP to run extraction queries and saves results as local parquet files. Since BigQuery MCP returns JSON, we convert to parquet via pandas.

**Step 1: Implement extraction module**

```python
# econometrics/extract.py
"""BigQuery extraction queries and parquet serialization.

Queries are designed to run via mcp__bigquery__execute-query.
This module provides the SQL strings and result-to-parquet conversion.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final, Sequence

import pandas as pd

from econometrics.types import (
    POOL_ADDRESS, START_BLOCK, END_BLOCK,
    MINT_TOPIC, BURN_TOPIC, SWAP_TOPIC, PARQUET_DIR,
)


# ── SQL Queries ────────────────────────────────────────────────────────

MINT_BURN_QUERY: Final = f"""
SELECT
    block_number,
    block_timestamp,
    transaction_hash,
    log_index,
    topics,
    data
FROM `bigquery-public-data.crypto_ethereum.logs`
WHERE
    address = '{POOL_ADDRESS}'
    AND block_number BETWEEN {START_BLOCK} AND {END_BLOCK}
    AND (
        topics[SAFE_OFFSET(0)] = '{MINT_TOPIC}'
        OR topics[SAFE_OFFSET(0)] = '{BURN_TOPIC}'
    )
ORDER BY block_number, log_index
"""

SWAP_QUERY: Final = f"""
SELECT
    block_number,
    block_timestamp,
    transaction_hash,
    log_index,
    topics,
    data
FROM `bigquery-public-data.crypto_ethereum.logs`
WHERE
    address = '{POOL_ADDRESS}'
    AND block_number BETWEEN {START_BLOCK} AND {END_BLOCK}
    AND topics[SAFE_OFFSET(0)] = '{SWAP_TOPIC}'
ORDER BY block_number, log_index
"""

JIT_TX_QUERY: Final = f"""
SELECT transaction_hash
FROM `bigquery-public-data.crypto_ethereum.logs`
WHERE
    address = '{POOL_ADDRESS}'
    AND block_number BETWEEN {START_BLOCK} AND {END_BLOCK}
    AND topics[SAFE_OFFSET(0)] IN ('{MINT_TOPIC}', '{BURN_TOPIC}')
GROUP BY transaction_hash
HAVING
    COUNTIF(topics[SAFE_OFFSET(0)] = '{MINT_TOPIC}') > 0
    AND COUNTIF(topics[SAFE_OFFSET(0)] = '{BURN_TOPIC}') > 0
"""

DAILY_JIT_INSTRUMENT_QUERY: Final = f"""
WITH jit_txs AS (
    SELECT transaction_hash, MIN(block_number) as block_number
    FROM `bigquery-public-data.crypto_ethereum.logs`
    WHERE
        address = '{POOL_ADDRESS}'
        AND block_number BETWEEN {START_BLOCK} AND {END_BLOCK}
        AND topics[SAFE_OFFSET(0)] IN ('{MINT_TOPIC}', '{BURN_TOPIC}')
    GROUP BY transaction_hash
    HAVING
        COUNTIF(topics[SAFE_OFFSET(0)] = '{MINT_TOPIC}') > 0
        AND COUNTIF(topics[SAFE_OFFSET(0)] = '{BURN_TOPIC}') > 0
)
SELECT
    CAST(FLOOR((block_number - {START_BLOCK}) / 7200) AS INT64) as day,
    COUNT(*) as jit_count
FROM jit_txs
GROUP BY day
ORDER BY day
"""

DAILY_SWAP_COUNT_QUERY: Final = f"""
SELECT
    CAST(FLOOR((block_number - {START_BLOCK}) / 7200) AS INT64) as day,
    COUNT(*) as swap_count
FROM `bigquery-public-data.crypto_ethereum.logs`
WHERE
    address = '{POOL_ADDRESS}'
    AND block_number BETWEEN {START_BLOCK} AND {END_BLOCK}
    AND topics[SAFE_OFFSET(0)] = '{SWAP_TOPIC}'
GROUP BY day
ORDER BY day
"""


# ── Parquet IO ─────────────────────────────────────────────────────────

def save_query_result(rows: Sequence[dict], filename: str) -> Path:
    """Save BigQuery result rows to parquet. Returns the file path."""
    out_dir = Path(PARQUET_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def load_parquet(filename: str) -> pd.DataFrame:
    """Load a parquet file from the data directory."""
    return pd.read_parquet(Path(PARQUET_DIR) / filename)
```

**Step 2: Commit**

```bash
git add econometrics/extract.py
git commit -m "feat(econometrics): BigQuery SQL queries and parquet IO"
```

---

## Task 3: JIT Classification — Same-Transaction

**Files:**
- Create: `econometrics/jit.py`
- Create: `tests/econometrics/test_jit.py`

**Step 1: Write the failing test**

```python
# tests/econometrics/test_jit.py
"""Tests for JIT LP classification — same-transaction mint+burn."""
from econometrics.types import MintEvent, BurnEvent, PositionLifecycle
from econometrics.jit import classify_jit


def _mint(block: int, tx: str, owner: str, tl: int, tu: int, amount: int) -> MintEvent:
    return MintEvent(block, tx, 0, owner, tl, tu, "0x", amount, 0, 0)


def _burn(block: int, tx: str, owner: str, tl: int, tu: int, amount: int) -> BurnEvent:
    return BurnEvent(block, tx, 1, owner, tl, tu, amount, 0, 0)


def test_same_tx_mint_burn_is_jit() -> None:
    """Mint and burn in the same transaction → JIT."""
    mints = [_mint(100, "0xtx1", "0xaaa", -100, 100, 1000)]
    burns = [_burn(100, "0xtx1", "0xaaa", -100, 100, 1000)]
    result = classify_jit(mints, burns)
    assert len(result) == 1
    assert result[0].is_jit is True
    assert result[0].blocklife == 1


def test_different_tx_same_block_is_not_jit() -> None:
    """Mint and burn in different txs, same block → NOT JIT."""
    mints = [_mint(100, "0xtx1", "0xaaa", -100, 100, 1000)]
    burns = [_burn(100, "0xtx2", "0xaaa", -100, 100, 1000)]
    result = classify_jit(mints, burns)
    assert len(result) == 1
    assert result[0].is_jit is False
    assert result[0].blocklife == 1


def test_multi_block_is_not_jit() -> None:
    """Mint at block 100, burn at block 200, same owner+ticks → not JIT."""
    mints = [_mint(100, "0xtx1", "0xbbb", -200, 200, 500)]
    burns = [_burn(200, "0xtx2", "0xbbb", -200, 200, 500)]
    result = classify_jit(mints, burns)
    assert len(result) == 1
    assert result[0].is_jit is False
    assert result[0].blocklife == 101


def test_unmatched_mint_excluded() -> None:
    """Mint with no matching burn → open position, not in output."""
    mints = [_mint(100, "0xtx1", "0xccc", -50, 50, 300)]
    burns: list[BurnEvent] = []
    result = classify_jit(mints, burns)
    assert len(result) == 0


def test_mixed_jit_and_passive() -> None:
    """Mix of JIT and passive positions classified correctly."""
    mints = [
        _mint(100, "0xtx1", "0xaaa", -10, 10, 1000),
        _mint(100, "0xtx3", "0xbbb", -20, 20, 500),
        _mint(200, "0xtx5", "0xccc", -30, 30, 200),
    ]
    burns = [
        _burn(100, "0xtx1", "0xaaa", -10, 10, 1000),   # same tx → JIT
        _burn(150, "0xtx4", "0xbbb", -20, 20, 500),     # diff tx → passive
        _burn(200, "0xtx5", "0xccc", -30, 30, 200),     # same tx → JIT
    ]
    result = classify_jit(mints, burns)
    jits = [r for r in result if r.is_jit]
    passives = [r for r in result if not r.is_jit]
    assert len(jits) == 2
    assert len(passives) == 1
```

**Step 2: Run test to verify failure**

```bash
python -m pytest tests/econometrics/test_jit.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'econometrics.jit'`

**Step 3: Implement JIT classification**

```python
# econometrics/jit.py
"""JIT LP classification — same-transaction mint+burn detection."""
from __future__ import annotations

from typing import Sequence

from econometrics.types import MintEvent, BurnEvent, PositionLifecycle


def classify_jit(
    mints: Sequence[MintEvent],
    burns: Sequence[BurnEvent],
) -> list[PositionLifecycle]:
    """Match Mint→Burn pairs and classify JIT.

    JIT = same transaction_hash for mint and burn (atomic mint→swap→burn).
    Matching key: (owner, tick_lower, tick_upper). FIFO within each group.
    Only completed lifecycles (matched mint+burn) are returned.
    """
    mint_queues: dict[tuple[str, int, int], list[MintEvent]] = {}
    for m in mints:
        key = (m.owner.lower(), m.tick_lower, m.tick_upper)
        mint_queues.setdefault(key, []).append(m)

    return [
        _make_lifecycle(mint_queues, b)
        for b in burns
        if _has_matching_mint(mint_queues, b)
    ]


def _has_matching_mint(
    queues: dict[tuple[str, int, int], list[MintEvent]],
    burn: BurnEvent,
) -> bool:
    key = (burn.owner.lower(), burn.tick_lower, burn.tick_upper)
    return bool(queues.get(key))


def _make_lifecycle(
    queues: dict[tuple[str, int, int], list[MintEvent]],
    burn: BurnEvent,
) -> PositionLifecycle:
    key = (burn.owner.lower(), burn.tick_lower, burn.tick_upper)
    mint = queues[key].pop(0)
    blocklife = burn.block_number - mint.block_number + 1
    is_jit = mint.tx_hash == burn.tx_hash

    return PositionLifecycle(
        owner=mint.owner.lower(),
        tick_lower=mint.tick_lower,
        tick_upper=mint.tick_upper,
        amount=mint.amount,
        mint_block=mint.block_number,
        burn_block=burn.block_number,
        mint_tx=mint.tx_hash,
        burn_tx=burn.tx_hash,
        blocklife=blocklife,
        is_jit=is_jit,
        theta=1.0 / blocklife,
    )
```

**Step 4: Run tests**

```bash
python -m pytest tests/econometrics/test_jit.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add econometrics/jit.py tests/econometrics/test_jit.py
git commit -m "feat(econometrics): JIT classification — same-transaction detection"
```

---

## Task 4: A_T Computation

**Files:**
- Create: `econometrics/concentration.py`
- Create: `tests/econometrics/test_concentration.py`

**Step 1: Write the failing test**

```python
# tests/econometrics/test_concentration.py
"""Tests for fee concentration index A_T."""
import math
from econometrics.types import PositionLifecycle
from econometrics.concentration import compute_a_t


def _lc(blocklife: int, fee_share: float) -> tuple[PositionLifecycle, float]:
    lc = PositionLifecycle(
        owner="0x", tick_lower=-100, tick_upper=100, amount=1000,
        mint_block=100, burn_block=100 + blocklife - 1,
        mint_tx="0xa", burn_tx="0xa" if blocklife == 1 else "0xb",
        blocklife=blocklife, is_jit=(blocklife == 1),
        theta=1.0 / blocklife,
    )
    return lc, fee_share


def test_single_jit_full_share() -> None:
    lc, share = _lc(1, 1.0)
    assert abs(compute_a_t([lc], [share]) - 1.0) < 1e-9


def test_single_passive_low_theta() -> None:
    lc, share = _lc(100, 1.0)
    assert abs(compute_a_t([lc], [share]) - 0.1) < 1e-9


def test_empty_gives_zero() -> None:
    assert compute_a_t([], []) == 0.0


def test_two_positions_mixed() -> None:
    pairs = [_lc(1, 0.6), _lc(10, 0.4)]
    lcs, shares = zip(*pairs)
    expected = math.sqrt(1.0 * 0.36 + 0.1 * 0.16)
    assert abs(compute_a_t(list(lcs), list(shares)) - expected) < 1e-9
```

**Step 2: Run test to verify failure**

```bash
python -m pytest tests/econometrics/test_concentration.py -v
```

**Step 3: Implement A_T**

```python
# econometrics/concentration.py
"""Fee concentration index A_T — pure computation."""
from __future__ import annotations

import math
from typing import Sequence

from econometrics.types import PositionLifecycle


def compute_a_t(
    lifecycles: Sequence[PositionLifecycle],
    fee_shares: Sequence[float],
) -> float:
    """Compute A_T = sqrt(sum_k theta_k * x_k^2).

    Args:
        lifecycles: Completed position lifecycles.
        fee_shares: Fee share per position (same order), summing to ~1.0.

    Returns:
        A_T in [0, 1].
    """
    if not lifecycles:
        return 0.0

    hhi_sum = sum(
        lc.theta * x * x
        for lc, x in zip(lifecycles, fee_shares, strict=True)
    )
    return math.sqrt(hhi_sum)


def approximate_equal_shares(n: int) -> list[float]:
    """Equal fee share approximation for pilot (1/n each)."""
    return [1.0 / n] * n if n > 0 else []
```

**Step 4: Run tests**

```bash
python -m pytest tests/econometrics/test_concentration.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add econometrics/concentration.py tests/econometrics/test_concentration.py
git commit -m "feat(econometrics): A_T fee concentration index computation"
```

---

## Task 5: Panel Assembly

**Files:**
- Create: `econometrics/panel.py`
- Create: `tests/econometrics/test_panel.py`

**Step 1: Write the failing test**

```python
# tests/econometrics/test_panel.py
"""Tests for panel dataset assembly."""
from econometrics.types import PositionLifecycle, PanelRow
from econometrics.panel import build_exit_panel


def _lc(owner: str, mint_b: int, burn_b: int, is_jit: bool) -> PositionLifecycle:
    bl = burn_b - mint_b + 1
    return PositionLifecycle(
        owner=owner, tick_lower=-100, tick_upper=100, amount=1000,
        mint_block=mint_b, burn_block=burn_b,
        mint_tx="0xa", burn_tx="0xa" if is_jit else "0xb",
        blocklife=bl, is_jit=is_jit, theta=1.0 / bl,
    )


def test_passive_burn_is_exit() -> None:
    lcs = [_lc("0xpassive", 100, 200, False)]
    a_t_map = {200: 0.5}
    jit_lag = {27: 3}  # day 27 ~ block 200
    swap_counts = {27: 50}
    panel = build_exit_panel(lcs, a_t_map, jit_lag, swap_counts)
    assert len(panel) == 1
    assert panel[0].exit == 1
    assert panel[0].a_t == 0.5


def test_jit_excluded() -> None:
    lcs = [_lc("0xjit", 100, 100, True), _lc("0xpassive", 100, 200, False)]
    panel = build_exit_panel(lcs, {100: 0.3, 200: 0.5}, {}, {})
    assert len(panel) == 1
    assert panel[0].owner == "0xpassive"
```

**Step 2: Run test to verify failure**

```bash
python -m pytest tests/econometrics/test_panel.py -v
```

**Step 3: Implement panel assembly**

```python
# econometrics/panel.py
"""Panel dataset assembly for structural logit estimation."""
from __future__ import annotations

from typing import Mapping, Sequence

from econometrics.types import (
    PositionLifecycle, PanelRow, BlockNumber,
    START_BLOCK, BLOCKS_PER_DAY,
)


def _block_to_day(block: BlockNumber) -> int:
    return (block - START_BLOCK) // BLOCKS_PER_DAY


def build_exit_panel(
    lifecycles: Sequence[PositionLifecycle],
    a_t_at_block: Mapping[BlockNumber, float],
    jit_count_by_day: Mapping[int, int],
    swap_count_by_day: Mapping[int, int],
) -> list[PanelRow]:
    """Build estimation panel from passive LP exit events.

    Each passive LP burn → one PanelRow with Y=1.
    JIT positions excluded (they're the treatment, not the outcome).
    """
    return [
        PanelRow(
            owner=lc.owner,
            block=lc.burn_block,
            exit=1,
            a_t=a_t_at_block.get(lc.burn_block, 0.0),
            blocklife=lc.blocklife,
            tick_lower=lc.tick_lower,
            tick_upper=lc.tick_upper,
            amount=lc.amount,
            jit_count_lag1=jit_count_by_day.get(_block_to_day(lc.burn_block) - 1, 0),
            swap_count=swap_count_by_day.get(_block_to_day(lc.burn_block), 0),
        )
        for lc in lifecycles
        if not lc.is_jit
    ]
```

**Step 4: Run tests**

```bash
python -m pytest tests/econometrics/test_panel.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add econometrics/panel.py tests/econometrics/test_panel.py
git commit -m "feat(econometrics): panel dataset assembly with JIT instrument"
```

---

## Task 6: Full Pipeline — Extract, Decode, Classify, Assemble

**Files:**
- Create: `econometrics/pipeline.py`

This is the orchestration script that ties everything together. It runs BigQuery queries via MCP (or loads from cached parquet), decodes events, classifies JIT, computes A_T, and builds the panel.

**Step 1: Implement pipeline**

```python
# econometrics/pipeline.py
"""Full pipeline: BigQuery → decode → classify → A_T → panel → parquet.

Usage (after BigQuery extraction via MCP):
    python -m econometrics.pipeline

Assumes parquet files already exist in data/econometrics/parquet/ from
MCP extraction. If not, run the extraction queries via BigQuery MCP first
and save results with extract.save_query_result().
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from econometrics.types import (
    MintEvent, BurnEvent, MINT_TOPIC, BURN_TOPIC, PARQUET_DIR, START_BLOCK,
    BLOCKS_PER_DAY,
)
from econometrics.decode import decode_mint, decode_burn
from econometrics.jit import classify_jit
from econometrics.concentration import compute_a_t, approximate_equal_shares
from econometrics.panel import build_exit_panel


def run_pipeline() -> pd.DataFrame:
    """Run the full pipeline from cached parquet files to panel DataFrame."""
    parquet_dir = Path(PARQUET_DIR)

    # ── Load raw events ────────────────────────────────────────────────
    print("Loading raw events from parquet...")
    raw_df = pd.read_parquet(parquet_dir / "mint_burn_events.parquet")
    print(f"  {len(raw_df):,} raw event logs")

    # ── Decode ─────────────────────────────────────────────────────────
    print("Decoding events...")
    mints: list[MintEvent] = []
    burns: list[BurnEvent] = []

    for row in raw_df.itertuples():
        topics = row.topics
        data = row.data
        block = row.block_number
        tx = row.transaction_hash
        idx = row.log_index

        if topics[0] == MINT_TOPIC:
            mints.append(decode_mint(topics, data, block, tx, idx))
        elif topics[0] == BURN_TOPIC:
            burns.append(decode_burn(topics, data, block, tx, idx))

    print(f"  {len(mints):,} Mints, {len(burns):,} Burns")

    # ── Classify JIT ───────────────────────────────────────────────────
    print("Classifying JIT positions...")
    lifecycles = classify_jit(mints, burns)
    jit_lcs = [lc for lc in lifecycles if lc.is_jit]
    passive_lcs = [lc for lc in lifecycles if not lc.is_jit]
    print(f"  {len(lifecycles):,} lifecycles: {len(jit_lcs)} JIT, {len(passive_lcs)} passive")

    # ── Compute rolling A_T ────────────────────────────────────────────
    print("Computing A_T per block window...")
    a_t_at_block: dict[int, float] = {}

    # Group lifecycles by daily window, compute A_T per window
    for lc in lifecycles:
        day = (lc.burn_block - START_BLOCK) // BLOCKS_PER_DAY
        day_start = START_BLOCK + day * BLOCKS_PER_DAY
        day_end = day_start + BLOCKS_PER_DAY

        window_lcs = [
            l for l in lifecycles
            if day_start <= l.burn_block < day_end
        ]
        if window_lcs:
            shares = approximate_equal_shares(len(window_lcs))
            a_t = compute_a_t(window_lcs, shares)
            a_t_at_block[lc.burn_block] = a_t

    # ── Load instrument data ───────────────────────────────────────────
    print("Loading JIT instrument and swap counts...")
    jit_daily = pd.read_parquet(parquet_dir / "daily_jit_instrument.parquet")
    swap_daily = pd.read_parquet(parquet_dir / "daily_swap_counts.parquet")

    jit_by_day = dict(zip(jit_daily["day"], jit_daily["jit_count"]))
    swap_by_day = dict(zip(swap_daily["day"], swap_daily["swap_count"]))

    # ── Build panel ────────────────────────────────────────────────────
    print("Assembling panel dataset...")
    panel_rows = build_exit_panel(lifecycles, a_t_at_block, jit_by_day, swap_by_day)
    panel_df = pd.DataFrame([vars(r) for r in panel_rows])

    out_path = parquet_dir / "panel.parquet"
    panel_df.to_parquet(out_path, index=False)
    print(f"  {len(panel_df):,} panel rows saved to {out_path}")

    return panel_df


if __name__ == "__main__":
    run_pipeline()
```

**Step 2: Commit**

```bash
git add econometrics/pipeline.py
git commit -m "feat(econometrics): full pipeline orchestration — extract to panel"
```

---

## Task 7: Structural Logit Estimation

**Files:**
- Create: `econometrics/estimate.py`
- Create: `tests/econometrics/test_estimate.py`

**Step 1: Write the failing test**

```python
# tests/econometrics/test_estimate.py
"""Tests for structural logit estimation."""
import numpy as np
from econometrics.estimate import structural_logit, EstimationResult


def test_positive_a_t_coefficient_on_synthetic_data() -> None:
    """On synthetic data where high A_T → exit, beta_3 should be positive."""
    rng = np.random.default_rng(42)
    n = 500
    a_t = rng.uniform(0, 1, n)
    swap_count = rng.poisson(50, n)
    jit_lag = rng.poisson(3, n)

    # Exit probability increases with A_T
    latent = 2.0 * a_t - 1.0 + rng.logistic(0, 1, n)
    exit_var = (latent > 0).astype(int)

    result = structural_logit(
        exit=exit_var,
        a_t=a_t,
        jit_instrument=jit_lag,
        swap_count=swap_count,
    )
    assert isinstance(result, EstimationResult)
    assert result.beta_concentration > 0  # A_T drives exit
    assert result.p_value_concentration < 0.05


def test_estimation_result_has_wtp() -> None:
    """Result should include dollar WTP estimate."""
    rng = np.random.default_rng(123)
    n = 300
    a_t = rng.uniform(0, 1, n)
    exit_var = (a_t + rng.logistic(0, 0.5, n) > 0.5).astype(int)

    result = structural_logit(
        exit=exit_var,
        a_t=a_t,
        jit_instrument=rng.poisson(2, n),
        swap_count=rng.poisson(40, n),
    )
    assert hasattr(result, 'wtp_mean')
    assert result.wtp_mean >= 0
```

**Step 2: Run test to verify failure**

```bash
python -m pytest tests/econometrics/test_estimate.py -v
```

**Step 3: Implement structural logit**

```python
# econometrics/estimate.py
"""Structural logit estimation for LP insurance demand.

Estimates: P(Exit=1) = Λ(β₁·SwapCount + β₂·IL + β₃·A_T + ε)
where β₃ is the concentration risk premium (WTP parameter).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
import statsmodels.api as sm
from numpy.typing import NDArray

FEE_REVENUE_PROXY: Final = 100.0  # Placeholder: avg daily fee revenue in USD per LP


@dataclass(frozen=True)
class EstimationResult:
    """Structural logit estimation output."""
    beta_concentration: float  # β₃ — parameter of interest
    se_concentration: float
    p_value_concentration: float
    beta_swap: float
    n_obs: int
    pseudo_r2: float
    wtp_mean: float  # β₃ × E[A_T] × FeeRevenue
    log_likelihood: float
    aic: float


def structural_logit(
    exit: NDArray[np.int_],
    a_t: NDArray[np.float64],
    jit_instrument: NDArray[np.int_],
    swap_count: NDArray[np.int_],
) -> EstimationResult:
    """Estimate structural logit of LP exit decision.

    For the pilot, this is a reduced-form logit (not IV). The IV extension
    requires a two-stage approach (first stage: JIT → A_T, second stage:
    instrumented A_T → exit) which is added in Tier 3.

    Args:
        exit: Binary outcome (1 = LP exits).
        a_t: Fee concentration index at exit event.
        jit_instrument: Lagged JIT count (instrument, used as control here).
        swap_count: Daily swap count (fee revenue proxy / control).
    """
    X = np.column_stack([a_t, swap_count.astype(float), jit_instrument.astype(float)])
    X = sm.add_constant(X)

    model = sm.Logit(exit, X)
    result = model.fit(disp=0)

    beta_3 = float(result.params[1])  # A_T coefficient
    se_3 = float(result.bse[1])
    p_3 = float(result.pvalues[1])
    beta_swap = float(result.params[2])

    mean_a_t = float(np.mean(a_t))
    wtp = beta_3 * mean_a_t * FEE_REVENUE_PROXY

    return EstimationResult(
        beta_concentration=beta_3,
        se_concentration=se_3,
        p_value_concentration=p_3,
        beta_swap=beta_swap,
        n_obs=len(exit),
        pseudo_r2=float(result.prsquared),
        wtp_mean=max(wtp, 0.0),
        log_likelihood=float(result.llf),
        aic=float(result.aic),
    )
```

**Step 4: Run tests**

```bash
python -m pytest tests/econometrics/test_estimate.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add econometrics/estimate.py tests/econometrics/test_estimate.py
git commit -m "feat(econometrics): structural logit estimation with WTP recovery"
```

---

## Task 8: MCP Extraction Script

**Files:**
- Create: `econometrics/run_extraction.py`

This script documents the exact MCP queries to run and how to save results. Since MCP queries are run interactively via Claude Code, this serves as the runbook.

**Step 1: Create runbook**

```python
# econometrics/run_extraction.py
"""Extraction runbook — run these queries via BigQuery MCP.

Each query should be executed via mcp__bigquery__execute-query,
then the result saved via extract.save_query_result().

Usage:
    1. Run each QUERY via BigQuery MCP in Claude Code
    2. Save results: extract.save_query_result(result, "filename.parquet")
    3. Run pipeline: python -m econometrics.pipeline
"""
from econometrics.extract import (
    MINT_BURN_QUERY,
    JIT_TX_QUERY,
    DAILY_JIT_INSTRUMENT_QUERY,
    DAILY_SWAP_COUNT_QUERY,
)

EXTRACTION_STEPS = [
    {
        "name": "Mint/Burn Events",
        "query": MINT_BURN_QUERY,
        "output": "mint_burn_events.parquet",
        "description": "All Mint and Burn events for ETH/USDC 30bps, blocks 21.35M-22M",
    },
    {
        "name": "Daily JIT Instrument",
        "query": DAILY_JIT_INSTRUMENT_QUERY,
        "output": "daily_jit_instrument.parquet",
        "description": "Daily JIT transaction count (instrument for A_T)",
    },
    {
        "name": "Daily Swap Counts",
        "query": DAILY_SWAP_COUNT_QUERY,
        "output": "daily_swap_counts.parquet",
        "description": "Daily swap count (fee revenue proxy / control)",
    },
]

if __name__ == "__main__":
    for step in EXTRACTION_STEPS:
        print(f"\n{'='*60}")
        print(f"Step: {step['name']}")
        print(f"Output: {step['output']}")
        print(f"Description: {step['description']}")
        print(f"{'='*60}")
        print(step["query"])
```

**Step 2: Commit**

```bash
git add econometrics/run_extraction.py
git commit -m "docs(econometrics): MCP extraction runbook with query definitions"
```

---

## Summary

| Task | Component | Tests | Depends On |
|------|-----------|-------|------------|
| 0 | Types, constants, env setup | — | — |
| 1 | Event decoding (pure functions) | test_decode.py | Task 0 |
| 2 | BigQuery SQL + parquet IO | — | Task 0 |
| 3 | JIT classification (same-tx) | test_jit.py | Task 0 |
| 4 | A_T computation | test_concentration.py | Task 0 |
| 5 | Panel assembly | test_panel.py | Tasks 3, 4 |
| 6 | Pipeline orchestration | — | Tasks 1-5 |
| 7 | Structural logit estimation | test_estimate.py | Task 5 |
| 8 | MCP extraction runbook | — | Task 2 |

**After implementation:** Run extraction queries via BigQuery MCP, execute pipeline, review estimation results.
