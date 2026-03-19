# ThetaSwap -- One-Shot Build Prompt

Copy everything below this line into your AI assistant to build the complete ThetaSwap frontend.

---

Build a React + Tailwind CSS application called **ThetaSwap** -- an insurance protocol frontend for passive Uniswap V4 liquidity providers hedging against JIT (just-in-time) liquidity extraction.

## Design System

### Colors
- **Primary**: slate (text, borders, accents)
- **Secondary**: amber (active states, severity mid-range, CTA highlights)
- **Neutral**: zinc (backgrounds, panels, borders)
- **Severity scale** for Delta-plus values: < 0.2 = zinc/muted, 0.2-0.5 = amber, 0.5-0.8 = orange, > 0.8 = red

### Typography
- **Headings**: `Instrument Serif` (italic for section titles)
- **Body**: `IBM Plex Sans`
- **Monospace/Numerics**: `IBM Plex Mono` -- ALL numeric values must use this font

### Theme
- Dark mode default: zinc-950 body background, zinc-900 panels, zinc-800 borders
- Dense, terminal-like aesthetic (Bloomberg meets arXiv)

## Application Structure

### Shell
- Collapsible left sidebar (240px -> 64px icon-only)
  - Logo "ThetaSwap" in Instrument Serif
  - Nav items: Pools (BarChart3 icon), Portfolio (Wallet icon), Research (BookOpen icon), Settings (Settings icon)
  - Active nav item: amber-500 text + left indicator bar
- Top bar (48px): breadcrumbs left, wallet connect + network indicator + theme toggle right
- Main content area fills remaining viewport (no max-width constraint)

### Section 1: Pool Explorer (default landing page, route: `/`)
Dense sortable table of monitored Uniswap V4 pools.

**Filter bar**: Search pair input, fee tier dropdown, vault status dropdown, pool count display.

**Table columns**: Pool Pair, Fee (bps), Delta-plus Epoch (severity-colored), Trend (inline SVG sparkline), theta-sum, Positions, TVL, 24h Vol, Vault (status badge: "Active + Xd" / "Settled" / dash).

**Interactions**: Click column headers to sort (ascending/descending toggle). Click row to drill down to Pool Terminal. Hover Delta-plus header shows methodology tooltip.

**Key types**:
```typescript
interface Pool {
  poolKey: string; pair: [string, string]; feeTier: number;
  deltaPlusEpoch: number; deltaPlus: number; sparkline: number[];
  thetaSum: number; atNull: number; removedPosCount: number;
  positionCount: number; tvl: number; volume24h: number;
  vault: PoolVault | null;
}
interface PoolVault {
  status: 'active' | 'settled' | 'none'; strike: number; expiry: number;
  hwm: number; totalDeposits: number; settled: boolean; longPayoutPerToken: number;
}
```

### Section 2: Pool Terminal (route: `/pool/:id`)
Three-pane split layout for deep pool analysis.

**Left pane (45%)**: Position table -- columns: Address, Tick Range, Liquidity, Fees (USDC), Blocks, Max Delta-plus. Sortable. User's own positions highlighted with amber left border. Row click expands accordion with details (ETH/USDC fees, raw liquidity, tick width, concentration classification).

**Right pane (55%)**: Stacked vertically:
1. **Oracle State**: Large Delta-plus Epoch display (severity-colored, 3 decimal places). Secondary metrics grid: Delta-plus Cumul., atNull, theta-sum, Removed count, Epoch progress bar, Last Poke timestamp.
2. **Vault**: Strike, HWM, Expiry countdown, Total Deposits, settlement status. Action buttons: Deposit (amber CTA), Redeem Pair, Poke. If settled: Redeem LONG (emerald), Redeem SHORT.
3. **Payoff Curve**: SVG chart -- LONG payout vs Delta-plus. Strike as vertical dashed line, current Delta-plus marker with severity color, HWM dot with label. Power-squared formula: max(0, ((HWM - K)/(1 - K))^2).

**Bottom strip (20% height)**: Full-width time series SVG -- Delta-plus line (amber), HWM line (slate, dashed), epoch boundaries (vertical dashed). Time range selector: 1D, 7D, 30D, All.

**Key types**:
```typescript
interface OracleState {
  deltaPlusEpoch: number; deltaPlusCumulative: number; atNull: number;
  thetaSum: number; removedPosCount: number; epochProgress: number;
  epochLength: number; epochStartTimestamp: number; lastPokeTimestamp: number;
}
interface VaultState {
  strike: number; hwm: number; expiry: number; totalDeposits: number;
  settled: boolean; longPayoutPreview: number; shortPayoutPreview: number;
}
interface Position {
  address: string; tickLower: number; tickUpper: number; liquidity: number;
  feeRevenue0: number; feeRevenue1: number; blockLifetime: number;
  maxDelta: number; isUser: boolean;
}
```

### Section 3: Portfolio (route: `/portfolio`)
**Summary strip**: 4 stat cards -- Total Deposited, LONG Value, SHORT Value, Net P&L (green/red colored).

**Active Vaults table**: Pool, LONG balance, SHORT balance, Strike, Expiry, Payout Preview (LONG% / SHORT%), Status badge. Click row navigates to Pool Terminal.

**Settled Vaults table**: Pool, Settlement date, LONG Payout, SHORT Payout, Net Result (emerald/red).

### Section 4: Research (route: `/research`)
Academic article layout, max-width 960px centered. Breaks from terminal aesthetic.

**Sections**: S1 Abstract (with 3 summary stat cards), S2 Methodology (data source, mechanism, payoff formula in KaTeX display mode), S3 Results (3 SVG charts: welfare bar chart, Delta-plus distribution histogram, payoff sensitivity line chart), S4 Calibration Parameters (table with LaTeX parameter names), S5 Conclusion.

**Dependencies**: `katex` package for LaTeX rendering. Import `katex/dist/katex.min.css`.

## Important Implementation Notes

1. All charts are SVG-based -- no external chart libraries
2. All numeric values in IBM Plex Mono with `tabular-nums`
3. Alternating row backgrounds (zinc-900/50 and zinc-950) for data density
4. Compact row heights (40-44px) for tables
5. No rounded corners on buttons/cards -- use `rounded-none` for the terminal aesthetic
6. Icons from `lucide-react`: BarChart3, Wallet, BookOpen, Settings, PanelLeftClose, PanelLeftOpen, ChevronUp, ChevronDown, Info, ChevronRight, Sun, Moon
7. Use sample data JSON files to render the UI with realistic mock data
