# Pool Terminal Tests

## Layout Tests

- [ ] Three-pane layout renders: left (45%), right (55%), bottom strip (20% height, min 120px)
- [ ] Left pane has `border-r border-zinc-800` separator
- [ ] Bottom strip has `border-t border-zinc-800` separator
- [ ] Full height fills container (`h-full flex flex-col`)

## Position Table (Left Pane)

### Header
- [ ] Shows "Positions" heading in Instrument Serif italic
- [ ] Shows position count, e.g. "18 positions"

### Columns
- [ ] Renders 6 column headers: Address, Tick Range, Liquidity, Fees (USDC), Blocks, Max Delta-plus
- [ ] All headers are sortable (click toggles direction)
- [ ] "Fees (USDC)" tooltip: "Cumulative fee revenue in token1 (USDC)"
- [ ] "Blocks" tooltip: "Block lifetime = blocks between position add and remove"
- [ ] "Max Delta-plus" tooltip: "Highest Delta-plus epoch observed during this position's lifetime"

### Data Display
- [ ] Address renders truncated (e.g., "0xe692...47C3")
- [ ] Tick range renders as "[tickLower, tickUpper]"
- [ ] Special tick values: -887220 renders as "MIN", 887220 as "MAX"
- [ ] Liquidity formatted with P/T/B/M suffixes (e.g., "892.0T")
- [ ] Fee revenue in USDC with 2 decimal places
- [ ] Block lifetime with locale number formatting
- [ ] Max Delta-plus severity-colored to 2 decimal places

### User Position Highlighting
- [ ] Positions with `isUser: true` have `border-l-2 border-l-amber-500`
- [ ] Sample data has 2 user positions (0xe692...47C3 and 0x5c4A...1E88)

### Row Expansion
- [ ] Click row toggles accordion expansion
- [ ] Expanded row shows 6-cell detail grid: ETH Fees, USDC Fees, Raw Liquidity, Tick Range, Width (ticks), Concentration
- [ ] Concentration classification: tick width <= 120 = "JIT-like", <= 1200 = "Concentrated", > 1200 = "Wide/Full range"
- [ ] Position with ticks [-60, 60] (width 120) shows "JIT-like"
- [ ] Position with ticks [-600, 600] (width 1200) shows "Concentrated"
- [ ] Position with ticks [-887220, 887220] shows "Wide/Full range"

## Oracle State (Right Pane, Top)

- [ ] "Oracle State" heading in Instrument Serif italic
- [ ] Delta-plus Epoch renders in 3xl font, severity-colored, 3 decimal places (e.g., "0.350")
- [ ] Label "Delta-plus Epoch" in 10px uppercase above the value
- [ ] Secondary metrics grid shows: Delta-plus Cumul., atNull, theta-sum, Removed count
- [ ] atNull has tooltip: "Competitive threshold: Delta-plus = max(0, A_T - atNull)"
- [ ] theta-sum has tooltip: "sum(1/block_lifetime_k) cumulative over position removals"
- [ ] Epoch progress bar renders with amber fill on zinc-800 track
- [ ] Epoch progress percentage label (e.g., "63%")
- [ ] Last Poke shows relative time (e.g., "15h ago")

## Vault Section (Right Pane, Middle)

### Pre-Settlement State
- [ ] "Vault" heading + "Active + Xd" badge in amber
- [ ] Shows Strike (3 decimal places), HWM (3 decimal places), Expiry countdown, Total Deposits (USD formatted)
- [ ] Three action buttons visible: "Deposit", "Redeem Pair", "Poke"
- [ ] "Deposit" button: amber CTA style (border-amber-500/40, bg-amber-500/10, text-amber-400)
- [ ] "Redeem Pair" button: secondary style (border-zinc-700, bg-zinc-800)
- [ ] "Poke" button: secondary style
- [ ] onDeposit fires when "Deposit" clicked
- [ ] onRedeemPair fires when "Redeem Pair" clicked
- [ ] onPoke fires when "Poke" clicked

### Post-Settlement State
- [ ] "Settled" badge replaces "Active" badge
- [ ] Two buttons visible: "Redeem LONG", "Redeem SHORT"
- [ ] "Redeem LONG" button: emerald CTA (border-emerald-500/40, bg-emerald-500/10)
- [ ] onRedeemLong fires when "Redeem LONG" clicked
- [ ] onRedeemShort fires when "Redeem SHORT" clicked

## Payoff Curve (Right Pane, Bottom)

- [ ] "Payoff Curve" heading in Instrument Serif italic
- [ ] Formula note: "LONG payout vs Delta-plus -- power-squared: max(0, ((HWM - K)/(1 - K))^2)"
- [ ] SVG renders with axes: Delta-plus (x, 0-1) vs LONG Payout (y, 0-1)
- [ ] Payoff line in amber (#fbbf24) with area fill at 6% opacity
- [ ] Strike line at x=0.25 (vertical dashed, slate)
- [ ] Strike label "K=0.25" above the line
- [ ] Current Delta-plus marker at x=0.35 (severity-colored dashed line + filled circle)
- [ ] HWM marker as open circle with "HWM" label
- [ ] Grid lines at y = 0, 0.25, 0.5, 0.75, 1.0

## Time Series (Bottom Strip)

### Controls
- [ ] "Delta-plus Time Series" heading in Instrument Serif italic
- [ ] Time range buttons: "1D", "7D", "30D", "All"
- [ ] Active range button: bg-zinc-700 text-slate-200
- [ ] Inactive range buttons: text-zinc-500

### Chart
- [ ] Delta-plus line in amber (#fbbf24), 1.5px stroke
- [ ] Delta-plus area fill at 6% opacity
- [ ] HWM line in slate (#64748b), 1px dashed stroke
- [ ] HWM area fill at 4% opacity
- [ ] Epoch boundaries as vertical dashed lines (#52525b)
- [ ] Legend at top: amber line = "Delta-plus", slate dashed = "HWM"
- [ ] Y-axis labels in IBM Plex Mono
- [ ] X-axis date labels in M/D format
- [ ] Range "1D" filters to last 24h of data
- [ ] Range "All" shows complete time series
