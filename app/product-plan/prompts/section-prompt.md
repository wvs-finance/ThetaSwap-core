# ThetaSwap -- Section-by-Section Build Prompts

Use these prompts individually to build one section at a time. Follow the order: Shell -> Pool Explorer -> Pool Terminal -> Portfolio -> Research.

---

## Prompt 1: Shell

Build the application shell for ThetaSwap, a DeFi insurance protocol dashboard.

Design tokens:
- Background: zinc-950 (body), zinc-900 (sidebar/topbar)
- Borders: zinc-800
- Text: slate-200 (primary), slate-400 (secondary)
- Active nav: amber-500 text + amber-500 left indicator bar
- Fonts: Instrument Serif (logo), IBM Plex Sans (nav labels)

Shell structure:
- Collapsible left sidebar (240px full, 64px collapsed). Logo "ThetaSwap" (Instrument Serif italic). Nav items: Pools (BarChart3 icon, default active), Portfolio (Wallet), Research (BookOpen). Separator. Settings (bottom). Collapse toggle button.
- Top bar (48px): Breadcrumbs (left), wallet connect button + network indicator dot + theme toggle (right).
- Main content area: flex-1, overflow auto.

Components: AppShell, MainNav, UserMenu. Icons from lucide-react.

---

## Prompt 2: Pool Explorer

Build the Pool Explorer section -- a dense, sortable, filterable table showing monitored Uniswap V4 pools with fee concentration (Delta-plus) metrics.

Must include: filter bar (search pair, fee tier dropdown, vault status dropdown), sortable column headers with sort direction indicators, inline SVG sparklines for Delta-plus trend, severity-colored Delta-plus values (< 0.2 zinc, 0.2-0.5 amber, 0.5-0.8 orange, > 0.8 red), vault status badges (Active with countdown / Settled / dash), methodology tooltip on Delta-plus header.

All numerics in IBM Plex Mono. Alternating row backgrounds. Click row fires onPoolClick callback.

See `sections/pool-explorer/types.ts` for the Pool, PoolVault, PoolExplorerProps, and PoolFilters interfaces. Use `sections/pool-explorer/sample-data.json` for mock data.

---

## Prompt 3: Pool Terminal

Build the Pool Terminal -- a three-pane split view for deep pool analysis.

Layout: Left pane (45%) = position table. Right pane (55%) = oracle state + vault controls + SVG payoff curve. Bottom strip (20% height) = time-series chart.

Position table: sortable by address, tick range, liquidity, fees, block lifetime, max Delta-plus. User positions have amber left border. Row click expands accordion with detail grid.

Oracle state: large Delta-plus Epoch display (severity-colored), secondary metrics grid, epoch progress bar.

Vault: strike, HWM, expiry, deposits. Buttons: Deposit (amber CTA), Redeem Pair, Poke. If settled: Redeem LONG (emerald), Redeem SHORT.

Payoff curve: SVG, LONG payout vs Delta-plus. Strike dashed line, current Delta-plus marker, HWM dot.

Time series: SVG, Delta-plus line (amber) + HWM line (slate dashed) + epoch boundaries. Range selector: 1D/7D/30D/All.

See `sections/pool-terminal/types.ts` and `sections/pool-terminal/sample-data.json`.

---

## Prompt 4: Portfolio

Build the Portfolio section -- aggregate view of user's LONG/SHORT positions across vaults.

Summary strip: 4 stat cards (Total Deposited, LONG Value, SHORT Value, Net P&L). P&L colored emerald/red.

Active Vaults table: Pool, LONG, SHORT, Strike, Expiry, Payout Preview (L%/S%), Status. Click navigates to Pool Terminal.

Settled Vaults table: Pool, Settlement date, LONG Payout, SHORT Payout, Net Result (emerald/red).

Same dense terminal aesthetic. Instrument Serif italic section headings. IBM Plex Mono for all values.

See `sections/portfolio/types.ts` and `sections/portfolio/sample-data.json`.

---

## Prompt 5: Research

Build the Research section -- an academic-style backtest report. This section DELIBERATELY breaks from the terminal aesthetic.

Layout: Single column, max-width 960px, centered. Instrument Serif headings with section numbers.

Content: S1 Abstract (summary paragraph + 3 stat cards). S2 Methodology (data source, mechanism, payoff formula in KaTeX display mode). S3 Results (3 SVG charts: welfare bar chart with error bars, Delta-plus distribution histogram with severity-colored bars, payoff sensitivity line chart). S4 Calibration Parameters (table with LaTeX-rendered parameter names). S5 Conclusion.

Requires `katex` package. Render LaTeX inline with `katex.render()` via useRef/useEffect.

See `sections/research/types.ts` and `sections/research/sample-data.json`.
