# Portfolio Tests

## Summary Strip

- [ ] Renders 4 stat cards in a horizontal row
- [ ] "Total Deposited" card shows "$4.25M"
- [ ] "LONG Value" card shows "$487.5K"
- [ ] "SHORT Value" card shows "$3.76M"
- [ ] "Net P&L" card shows "-$12.3K" in red-400 (negative value)
- [ ] Positive P&L would render in emerald-400 with "+" prefix
- [ ] Card labels use Instrument Serif italic (xs, zinc-500)
- [ ] Card values use IBM Plex Mono (xl, tabular-nums)
- [ ] Cards have `border border-zinc-800 bg-zinc-900 rounded-none`

## Active Vaults Table

### Structure
- [ ] "Active Vaults" heading in Instrument Serif italic
- [ ] Vault count shows "4 vaults"
- [ ] 7 column headers: Pool, LONG, SHORT, Strike, Expiry, Payout Preview, Status
- [ ] Column headers: text-xs font-medium uppercase tracking-wider text-slate-500

### Data Display
- [ ] Pool column shows pair name + fee tier: "ETH / USDC 30bps"
- [ ] LONG and SHORT balance columns formatted with K/M suffixes
- [ ] Strike renders to 2 decimal places: "0.25"
- [ ] Expiry shows days until: "14d" or "Expired"
- [ ] Payout Preview shows "22.5% / 77.5%" with amber-400 (LONG) / slate-400 (SHORT) colors
- [ ] Status badge shows "Active" in amber on amber/15 background

### Interactions
- [ ] Click row fires onVaultClick with pool tuple (e.g., ["ETH", "USDC"])
- [ ] Rows have cursor-pointer style
- [ ] Row hover: bg-zinc-800/60
- [ ] Alternating row backgrounds

## Settled Vaults Table

### Conditional Rendering
- [ ] Section only renders when settledVaults.length > 0
- [ ] "Settled Vaults" heading in Instrument Serif italic
- [ ] Shows count: "2 settled"

### Data Display
- [ ] 5 column headers: Pool, Settlement, LONG Payout, SHORT Payout, Net Result
- [ ] Pool column shows pair name: "CRV / USDC"
- [ ] Settlement date formatted as YYYY-MM-DD
- [ ] Payout values formatted as USD: "$42.2K", "$7.9K"
- [ ] CRV/USDC Net Result: "+$34.3K" in emerald-400 (positive)
- [ ] LINK/ETH Net Result: "-$43.6K" in red-400 (negative)
- [ ] Positive results have "+" prefix

### Interactions
- [ ] Click settled vault row fires onVaultClick
- [ ] Alternating row backgrounds

## Layout
- [ ] Full height container with flex-col
- [ ] Summary strip has border-b border-zinc-800
- [ ] Tables section is flex-1 overflow-auto
- [ ] Same dense terminal aesthetic as Pool Explorer
