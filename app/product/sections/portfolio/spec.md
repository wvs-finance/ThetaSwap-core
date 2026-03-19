# Portfolio

## Overview

User's aggregate LONG/SHORT positions across all vaults with P&L tracking. Summary strip shows total exposure at a glance, followed by active and settled vault tables. No deposit/redeem actions here -- users navigate to Pool Terminal for vault interactions.

## User Flows

1. **Check aggregate exposure** -- View total USDC deposited, LONG value, SHORT value, and net P&L
2. **Preview payouts** -- See current payout previews across all active vaults
3. **Drill down** -- Click any vault row to navigate to that pool's Terminal
4. **Review settled performance** -- Examine historical vault results to evaluate hedging effectiveness

## UI Requirements

### Summary Strip
- 4 stat cards in a horizontal row
- Total USDC Deposited, LONG Value, SHORT Value, Net P&L
- Large monospace values, Instrument Serif labels
- P&L card: green for positive, red for negative

### Active Vaults Table
- Columns: Pool pair, LONG balance, SHORT balance, vault status, strike, expiry, payout preview (LONG / SHORT)
- Same dense table aesthetic as Pool Explorer
- Click row to navigate to Pool Terminal

### Settled Vaults Section
- Below active vaults
- Columns: Pool, settlement date, LONG payout received, SHORT payout received, net result
- Net result colored: emerald for positive, red for negative

## Design Notes
- Same terminal aesthetic as Pool Explorer (dense, dark, monospace numerics)
- Section headings in Instrument Serif italic
- All numeric values in IBM Plex Mono
- Dark mode primary

## Configuration
- shell: false
