# ThetaSwap Frontend — Design OS

Refer to @agents.md for the design-os workflow and slash commands.

## Parent Project Context (REQUIRED)

This app lives inside the ThetaSwap monorepo at `app/`. **Before running any design-os command** (`/product-vision`, `/shape-section`, `/design-screen`, etc.), you MUST read from the parent directory to understand the protocol:

### Required Reading (relative to this directory)
- `../specs/` — Contract specifications per feature (001-FCI, 002-CFMM, 003-Reactive)
- `../research/model/` — LaTeX specification and PDF (the formal math model)
- `../research/backtest/` — Insurance backtest pipeline (8 modules)
- `../research/econometrics/` — Duration, hazard, cross-pool analysis (13 modules)
- `../research/notebooks/` — Jupyter notebooks with empirical results
- `../src/` — Solidity contracts (the actual protocol implementation)
- `../docs/plans/` — Branch-specific design plans
- `../CLAUDE.md` — Monorepo development guidelines

### How to Use Parent Context
- When defining product vision, pull problem statements and feature descriptions from the specs and research model
- When shaping sections, reference the actual contract interfaces and data structures in `../src/`
- When designing screens, use real metric names, formula notation, and data patterns from the research artifacts
- The research notebooks contain real backtest results — use those as the basis for sample data in screen designs

## Product Definition

### What We're Building
An **insurance protocol for passive liquidity providers** (LPs) on Uniswap V4. Passive LPs lose value when just-in-time (JIT) liquidity snipers front-run their positions. ThetaSwap provides a hedging mechanism — a derivative/insurance product — so passive LPs can protect themselves against this adverse selection.

### Core Protocol Concepts
- **Fee Concentration Index (FCI)**: Measures how concentrated fee collection is among LPs — high FCI means JIT snipers are dominating
- **Oracle Payoff**: Insurance payoff derived from on-chain FCI oracle readings
- **Custodian Vault**: Holds LP positions and manages insurance coverage
- **Reactive Integration**: Cross-chain event monitoring (Uniswap V3/V4 events trigger insurance state changes)

### Target Users
- **Institutional LPs** and **DeFi treasuries** managing large passive positions
- **Quantitative researchers** evaluating JIT risk and hedging strategies
- **Protocol teams** seeking to protect their liquidity incentive programs

These users are **math-heavy, quant-oriented, and research-driven**. They read whitepapers, understand Greeks, and evaluate protocols through empirical rigor.

## Aesthetic Direction

### Visual Identity: Research, Rigor, Academia
The UI should feel like a **quantitative research terminal meets academic paper** — not a typical DeFi dashboard.

**Tone**: Scholarly, precise, trustworthy. Think Bloomberg Terminal meets arXiv paper meets institutional risk management platform.

**Design Principles**:
- **Data density over decoration** — show more information, not more chrome
- **Typographic hierarchy is paramount** — mathematical notation, monospace for values, serif or academic typefaces for headings
- **Muted, institutional palette** — no neon gradients, no "crypto bro" aesthetics. Think slate, ink, parchment, with sharp accent colors for risk indicators
- **Charts and formulas are first-class citizens** — payoff diagrams, distribution plots, and LaTeX-style notation should feel native
- **Whitespace signals confidence** — generous margins, clean grids, no visual clutter
- **Dark mode primary** — quants work late; dark mode is the default, light mode is the alternative

**Anti-patterns (DO NOT use)**:
- Flashy DeFi dashboards with gradient cards and token logos everywhere
- Gamified UI elements (progress bars, achievement badges, confetti)
- Generic "Web3" aesthetics (purple gradients, neon accents, floating orbs)
- Oversimplified interfaces that hide complexity — our users WANT the complexity

**Inspiration**:
- Bloomberg Terminal (data density, keyboard-driven)
- Quantopian/QuantConnect (research notebooks as UI)
- Two Sigma / Citadel research portals (institutional, rigorous)
- Academic journal layouts (clear hierarchy, citation-style references)
- Observatory/scientific instrument dashboards (precision, measurement)
