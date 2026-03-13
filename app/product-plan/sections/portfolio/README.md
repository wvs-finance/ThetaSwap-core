# Portfolio

User's aggregate LONG/SHORT positions across all vaults with P&L tracking. Summary strip shows total exposure at a glance, followed by active and settled vault tables. No deposit/redeem actions here -- users navigate to Pool Terminal for vault interactions.

## User Flows

1. **Check aggregate exposure** -- View total USDC deposited, LONG value, SHORT value, and net P&L
2. **Preview payouts** -- See current payout previews across all active vaults
3. **Drill down** -- Click any vault row to navigate to that pool's Terminal
4. **Review settled performance** -- Examine historical vault results to evaluate hedging effectiveness

## UI Sections

### Summary Strip
4 stat cards: Total Deposited, LONG Value, SHORT Value, Net P&L (green/red).

### Active Vaults Table
Columns: Pool, LONG, SHORT, Strike, Expiry, Payout Preview, Status.

### Settled Vaults Table
Columns: Pool, Settlement date, LONG Payout, SHORT Payout, Net Result.

## Dependencies

- No additional icons beyond what the shell provides
