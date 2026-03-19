# ThetaSwap -- One-Shot Build Instructions

Build the complete ThetaSwap frontend in a single pass. This document provides all context needed.

## Prerequisites

```bash
# Create project
npm create vite@latest thetaswap -- --template react-ts
cd thetaswap
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install lucide-react katex
npm install -D @types/katex
```

## Font Setup

Add to `index.html` `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet" />
```

## Tailwind Configuration

In your main CSS file:
```css
@import "tailwindcss";
@import "katex/dist/katex.min.css";

@theme {
  --font-heading: 'Instrument Serif', serif;
  --font-body: 'IBM Plex Sans', sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
}
```

## Project Structure

```
src/
  shell/
    components/
      AppShell.tsx        -- Root layout: sidebar + topbar + content area
      MainNav.tsx         -- Sidebar navigation with collapsible state
      UserMenu.tsx        -- Wallet connect, network indicator, theme toggle
      index.ts
  sections/
    pool-explorer/
      components/
        PoolExplorer.tsx  -- Sortable/filterable pool table with sparklines
        index.ts
      types.ts
    pool-terminal/
      components/
        PoolTerminal.tsx  -- Three-pane split: positions, oracle/vault, charts
        index.ts
      types.ts
    portfolio/
      components/
        Portfolio.tsx     -- Summary strip + active/settled vault tables
        index.ts
      types.ts
    research/
      components/
        Research.tsx      -- Academic article with KaTeX and SVG charts
        index.ts
      types.ts
  App.tsx                 -- Router + state management
```

## Build Order

1. **Design tokens** -- Set up Tailwind theme, CSS custom properties, font imports
2. **Shell** -- AppShell with sidebar nav, topbar, content slot
3. **Pool Explorer** -- Dense table with sorting, filtering, sparklines, severity colors
4. **Pool Terminal** -- Three-pane layout: positions, oracle/vault/payoff, time series
5. **Portfolio** -- Summary cards + vault tables with P&L tracking
6. **Research** -- Academic article with KaTeX formulas and static SVG charts
7. **Integration** -- Router wiring, state management, drill-down navigation

## ThetaSwap-Specific Implementation Notes

### Delta-plus (Fee Concentration Index)
- Range: 0.0 (competitive) to 1.0 (fully extracted)
- Severity colors: < 0.2 = zinc/muted, 0.2-0.5 = amber, 0.5-0.8 = orange, > 0.8 = red
- Two variants: `deltaPlusEpoch` (resets each epoch) and `deltaPlus` (cumulative/lifetime)
- Derived from theta-sum: theta = sum(1/block_lifetime_k), A_T = sqrt(theta), Delta-plus = max(0, A_T - atNull)

### Vault Operations
- **Deposit**: User deposits USDC, receives equal LONG + SHORT tokens (ERC-6909)
- **Redeem Pair**: Burns equal LONG + SHORT, returns USDC (pre-settlement only)
- **Poke**: Permissionless oracle update -- triggers HWM comparison
- **Redeem LONG/SHORT**: Post-settlement redemption with payout based on payoff formula

### Payoff Formula
```
p(HWM, K) = max(0, ((HWM - K) / (1 - K))^2)
```
Where HWM = high-water mark of Delta-plus within epoch, K = strike threshold. LONG payout = p, SHORT payout = 1 - p.

### Oracle State Fields
- `deltaPlusEpoch`: Current epoch-scoped Delta-plus (primary metric)
- `deltaPlusCumulative`: Lifetime Delta-plus
- `atNull`: Competitive null threshold (baseline subtracted from raw index)
- `thetaSum`: Cumulative sum of 1/block_lifetime across position removals
- `removedPosCount`: Number of positions removed (used in index computation)
- `epochProgress`: Fraction of current epoch elapsed (0.0 to 1.0)

### Position Classification
- `blockLifetime <= 3`: JIT-like (extremely short-lived, likely MEV)
- `blockLifetime <= ~1200`: Concentrated (active management)
- `blockLifetime > 1200`: Wide/full range (passive)

## Sample Data

Load sample data from the JSON files in each section directory. Wire up callbacks for:
- `onPoolClick`: Navigate from Pool Explorer to Pool Terminal
- `onDeposit`, `onRedeemPair`, `onPoke`: Vault operation handlers (mock/log)
- `onVaultClick`: Navigate from Portfolio to Pool Terminal
- Sort and filter state is managed locally within each component
