# Step 3: Pool Terminal

## Goal
Build the Pool Terminal -- a three-pane split view for deep analysis of a single pool. Shows positions, oracle state, vault controls, payoff curve, and time series.

## Layout

```
+---------------------------+---------------------------+
|                           |                           |
|   LEFT PANE (45%)         |   RIGHT PANE (55%)        |
|   Position Table          |   Oracle State (top)      |
|                           |   Vault Controls (mid)    |
|                           |   Payoff Curve (bottom)   |
|                           |                           |
+-----------------------------------------------------------+
|   BOTTOM STRIP (20% height, min 120px)                    |
|   Delta-plus Time Series + HWM                            |
+-----------------------------------------------------------+
```

## Left Pane: Position Table

### Header
"Positions" in Instrument Serif italic + position count in monospace.

### Table Columns (6 columns)
1. **Address** (sortable): Truncated address with expand chevron (ChevronRight, rotates 90deg when expanded)
2. **Tick Range** (sortable by width): `[tickLower, tickUpper]`. Special values: -887220 = "MIN", 887220 = "MAX"
3. **Liquidity** (sortable, right): Formatted with P/T/B/M suffixes
4. **Fees (USDC)** (sortable, right): `feeRevenue1` with 2 decimal places
5. **Blocks** (sortable, right): `blockLifetime` with locale formatting
6. **Max Delta-plus** (sortable, right): Severity-colored, 2 decimal places

### Position Row Features
- User's own positions: `border-l-2 border-l-amber-500`
- Click row: toggles inline accordion expansion
- Expanded detail: 3-column grid showing ETH Fees, USDC Fees, Raw Liquidity, Tick Range, Width (ticks), Concentration classification (JIT-like / Concentrated / Wide)
- Concentration classification: tick width <= 120 = "JIT-like", <= 1200 = "Concentrated", else "Wide/Full range"

## Right Pane: Oracle + Vault + Payoff

### Oracle State Section
- **Primary display**: Delta-plus Epoch in 3xl monospace, severity-colored, 3 decimal places
- **Secondary metrics grid** (2 columns): Delta-plus Cumul., atNull (with tooltip), theta-sum (with tooltip), Removed count
- **Epoch progress bar**: Amber fill on zinc-800 track, percentage label
- **Last Poke**: Relative time ("12m ago", "3h ago")

### Vault Section
- **Header**: "Vault" title + status badge (Active with expiry countdown, or Settled)
- **Metrics grid** (2 columns): Strike, HWM, Expiry countdown, Total Deposits (formatted USD)
- **Pre-settlement buttons**: Deposit (amber CTA with `bg-amber-500/10 border-amber-500/40`), Redeem Pair (zinc), Poke (zinc)
- **Post-settlement buttons**: Redeem LONG (emerald, `bg-emerald-500/10 border-emerald-500/40`), Redeem SHORT (zinc)
- All buttons: `rounded-none` for terminal aesthetic

### Payoff Curve (SVG, ~280x160 viewport)
- **Axes**: Delta-plus (x, 0 to 1) vs LONG Payout (y, 0 to 1)
- **Payoff line**: Amber stroke (1.5px) with area fill at 6% opacity
- **Strike marker**: Vertical dashed line (slate) with "K=0.25" label
- **Current Delta-plus**: Vertical dashed line + filled circle (severity-colored)
- **HWM marker**: Open circle (slate stroke) with "HWM" label
- **Grid lines**: Horizontal at 0, 0.25, 0.5, 0.75, 1.0
- **Formula note**: Below chart: "LONG payout vs Delta-plus -- power-squared: max(0, ((HWM - K)/(1 - K))^2)"

## Bottom Strip: Time Series (SVG)

- **Delta-plus line**: Amber stroke (1.5px) with area fill (6% opacity)
- **HWM line**: Slate stroke (1px, dashed 3,2)
- **Epoch boundaries**: Vertical dashed lines (zinc-600)
- **Range selector**: 1D / 7D / 30D / All toggle buttons (top right of strip)
- **Legend**: Inline at top -- amber line = "Delta-plus", slate dashed = "HWM"
- **Y-axis**: Delta-plus values. **X-axis**: Date labels (M/D format)
- SVG: `preserveAspectRatio="none"`, height fills container

## Verification
- Position table sorts correctly by each column
- User positions (isUser: true) show amber left border
- Expanding a JIT-like position (blockLifetime=1) shows "JIT-like" classification
- Oracle Delta-plus 0.35 renders in amber-400
- Vault "Deposit" button visible when not settled, "Redeem LONG/SHORT" when settled
- Payoff curve strike line at x=0.25, current Delta-plus dot at x=0.35
- Time series shows epoch resets (Delta-plus drops, HWM resets)
- Range selector filters time series data
