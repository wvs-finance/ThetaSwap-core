# Pool Terminal

## Overview

Deep dive into a single pool. All data visible in one dense, terminal-like view. Three-pane split layout showing LP positions, oracle/vault state, payoff curve, and time-series charts. Users arrive here after clicking a pool row in the Pool Explorer.

## User Flows

1. **Inspect positions** -- View all LP positions in the pool, sort by any column, expand rows to see position detail
2. **Monitor oracle state** -- Watch Δ⁺ epoch severity, cumulative Δ⁺, competitive threshold (atNull), removed position count, epoch progress
3. **Manage vault** -- View strike, HWM, expiry countdown, total deposits. Execute deposit, redeem pair, poke. If settled: redeem LONG/SHORT with payout preview
4. **Analyze payoff** -- View LONG payout as function of Δ⁺ on a derivatives-style payoff curve with strike and HWM markers
5. **Track history** -- View Δ⁺ and HWM over time with epoch boundaries, toggle overlays, select time range

## Layout

Three-pane split:

### Left Pane (45% width) -- Position Table
- All LP positions in this pool
- Columns: address (truncated), tick range, liquidity, fee revenue (token0 + token1), block lifetime, max Δ⁺ experienced
- Sortable by any column
- Highlight user's own positions if wallet connected (amber left border)
- Row click expands inline accordion showing position detail

### Right Pane (35% width) -- Oracle & Vault

**Oracle State** (top):
- Current Δ⁺ epoch (from getDeltaPlusEpoch) -- large, prominent numeric display
- Δ⁺ cumulative (from getDeltaPlus) -- secondary/smaller display
- atNull (competitive threshold)
- removedPosCount (secondary metric)
- Epoch progress bar (time remaining in current epoch)
- Last poke timestamp

**Vault** (middle):
- Strike price, HWM (formatted as Δ⁺ equivalent)
- Expiry countdown
- Total deposits (from totalDeposited())
- Settlement status
- Action buttons: Deposit, Redeem Pair, Poke
- If settled: Redeem LONG / Redeem SHORT with payout preview

**Payoff Curve** (bottom):
- SVG chart showing LONG payout as function of Δ⁺
- Current Δ⁺ marked on curve
- Strike marked as vertical dashed line
- HWM marked as dot on curve
- Styled like a derivatives payoff diagram (clean axes, labels)

### Bottom Strip (20% height) -- Time Series
- Full-width SVG chart area
- Δ⁺ over time (primary line, amber)
- HWM over time (secondary line, slate, monotonically non-decreasing within epoch)
- Epoch boundaries as vertical dashed lines
- Time range selector: 1D, 7D, 30D, All

## Data Sources (Solidity Interfaces)

### IFeeConcentrationIndex
- `getIndex(key, reactive)` -> (indexA, thetaSum, removedPosCount)
- `getDeltaPlus(key, reactive)` -> deltaPlus (Q128)
- `getDeltaPlusEpoch(key, reactive)` -> deltaPlus epoch-reset (Q128)
- `getAtNull(key, reactive)` -> atNull (Q128)

### ICollateralCustodian
- `deposit(amount)` -- deposit USDC, receive LONG + SHORT
- `redeemPair(amount)` -- burn equal LONG + SHORT, receive USDC
- `totalDeposited()` -> uint128

### IOraclePayoff
- `poke()` -- permissionless HWM update
- `settle()` -- settle after expiry
- `redeemLong(amount)` / `redeemShort(amount)` -- post-settlement redemption
- `previewLongPayout(amount)` / `previewShortPayout(amount)` -> payout
- `payoffRatio()` -> (longPerToken, shortPerToken) in Q96
- `isSettled()` -> bool

### OraclePayoffStorage
- sqrtPriceStrike, sqrtPriceHWM, expiry, settled, longPayoutPerToken, poolKey, reactive

## Design Notes
- Dense, terminal-like aesthetic (Bloomberg meets arXiv)
- Dark mode primary: zinc-950 background, zinc-900 panels, zinc-800 borders
- Fonts: Instrument Serif for headings, IBM Plex Sans for body, IBM Plex Mono for ALL numeric values
- Colors: slate primary, amber accent, zinc neutral
- Severity coloring for Δ⁺: < 0.2 zinc, 0.2-0.5 amber, 0.5-0.8 orange, > 0.8 red
- Payoff curve and time-series are SVG-based (no external chart libraries)
- Tooltips on hoverable metrics showing formula/methodology

## Configuration
- shell: false
