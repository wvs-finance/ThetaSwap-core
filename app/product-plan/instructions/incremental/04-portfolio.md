# Step 4: Portfolio

## Goal
Build the Portfolio section -- aggregate view of user's LONG/SHORT token positions across all insurance vaults, with P&L tracking.

## Component: Portfolio.tsx

### Summary Strip
4 stat cards in a horizontal flex row, `border-b border-zinc-800`, padding 16px:

1. **Total Deposited**: USDC value, e.g. "$4.25M"
2. **LONG Value**: Current mark-to-market of LONG tokens
3. **SHORT Value**: Current mark-to-market of SHORT tokens
4. **Net P&L**: Color-coded -- emerald-400 if positive (prefix "+"), red-400 if negative

Each card:
- Label: Instrument Serif italic, xs, zinc-500
- Value: IBM Plex Mono, xl, tabular-nums, slate-200 (or emerald/red for P&L)
- Border: `border border-zinc-800 bg-zinc-900 rounded-none`

### Active Vaults Table

**Header**: "Active Vaults" (Instrument Serif italic) + vault count (IBM Plex Mono, zinc-500)

**Columns** (7):
1. **Pool** (left): Pair name + fee tier in small monospace, e.g. "ETH / USDC 30bps"
2. **LONG** (right): Token balance, formatted with K/M suffixes
3. **SHORT** (right): Token balance
4. **Strike** (right): 2 decimal places
5. **Expiry** (right): Days until expiry, e.g. "14d" or "Expired"
6. **Payout Preview** (right): "22.5% / 77.5%" in amber-400 / slate-400
7. **Status**: Badge -- "Active" in amber on amber/15 background

Row click: `onVaultClick(pool)` to navigate to Pool Terminal.

### Settled Vaults Table

Only renders if `settledVaults.length > 0`.

**Header**: "Settled Vaults" (Instrument Serif italic) + count

**Columns** (5):
1. **Pool** (left): Pair name
2. **Settlement** (right): Date formatted YYYY-MM-DD
3. **LONG Payout** (right): USD formatted
4. **SHORT Payout** (right): USD formatted
5. **Net Result** (right): Color-coded emerald/red with +/- prefix

Row click: `onVaultClick(pool)`.

### Styling
- Same table aesthetic as Pool Explorer (alternating rows, compact height, sticky headers)
- All numerics in IBM Plex Mono with tabular-nums
- Section headings in Instrument Serif italic

## Verification
- Summary strip shows 4 cards with correct formatting
- Net P&L card shows "-$12.3K" in red-400 (sample data is negative)
- Active vaults table has 4 rows
- Payout preview shows LONG% / SHORT% with amber / slate colors
- Settled vaults section shows 2 rows
- CRV/USDC settled vault: Net Result "+$34.3K" in emerald-400
- LINK/ETH settled vault: Net Result "-$43.6K" in red-400
- All rows are clickable
