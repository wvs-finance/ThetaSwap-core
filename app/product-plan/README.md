# ThetaSwap Product Plan Export

Self-contained export package for rebuilding the ThetaSwap frontend in any React + Tailwind project.

## What is ThetaSwap?

Insurance protocol for passive Uniswap V4 liquidity providers hedging against just-in-time (JIT) liquidity extraction. ThetaSwap quantifies fee concentration risk with an on-chain oracle (the Fee Concentration Index, Delta-plus) and offers paired LONG/SHORT tokens that settle based on observed severity.

## Package Contents

| Directory | Purpose |
|-----------|---------|
| `product-overview.md` | Product vision, problems solved, key features |
| `prompts/` | Copy-paste prompts for one-shot or section-by-section builds |
| `instructions/` | Detailed build instructions (one-shot and incremental) |
| `design-system/` | CSS tokens, Tailwind color palette, font configuration |
| `data-shapes/` | TypeScript types and entity relationship overview |
| `shell/` | Application shell components (sidebar nav, top bar, user menu) |
| `sections/` | Four feature sections with components, types, tests, and sample data |

## Sections (in order)

1. **Pool Explorer** -- Dense sortable table of monitored pools with severity-colored Delta-plus
2. **Pool Terminal** -- Three-pane split: positions, oracle/vault/payoff, time-series
3. **Portfolio** -- Summary strip + active/settled vault tables
4. **Research** -- Academic article with KaTeX formulas and SVG charts

## How to Use

### Option A: One-Shot Build
Copy `prompts/one-shot-prompt.md` into your AI assistant. It contains the full context to build the entire app in a single pass.

### Option B: Incremental Build
Follow `instructions/incremental/01-shell.md` through `05-research.md` in order. Each step builds on the previous.

## Design System

- **Colors**: Primary slate, secondary amber, neutral zinc
- **Fonts**: Instrument Serif (headings), IBM Plex Sans (body), IBM Plex Mono (numerics)
- **Theme**: Dark mode default (zinc-950 background)
- **Aesthetic**: Dense terminal-like interface (Bloomberg meets arXiv)

## Dependencies

- React 18+
- Tailwind CSS 3+
- lucide-react (icons)
- katex (Research section only -- LaTeX rendering)
