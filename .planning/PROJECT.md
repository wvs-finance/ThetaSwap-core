# ThetaSwap Presentation

## What This Is

A presentation package for ThetaSwap — an adverse competition oracle and insurance protocol for liquidity providers across all AMM pools and protocols. The presentation targets a mixed audience (technical and non-technical) and covers the problem, research summary, solution architecture, live demo, and roadmap. Deliverables include mermaid diagrams (architecture context + sequence), README updates, a demo script (running existing integration tests), and slide content.

## Core Value

Communicate that ThetaSwap builds the first on-chain, real-time fee concentration index that enables derivatives and insurance products so passive liquidity providers can hedge adverse competition — a risk orthogonal to LVR/impermanent loss.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Synthesize research into presentation-ready problem statement (econometric demand identification, inverted-U, turning point)
- [ ] Create architecture context diagram (mermaid) showing FCI hook, vault, CFMM, and protocol adapters
- [ ] Create sequence diagram (mermaid) for pool listening flow — from `listenPool()` through swap/mint/burn events to metric tracking
- [ ] Update README.md with architecture section containing the mermaid diagrams
- [ ] Identify and document the demo test (`NativeV4FeeConcentrationIndex.integration.t.sol`) with run instructions
- [ ] Define roadmap slide content: missing CFMM (optimal payoff formula), missing vault settlement mechanism
- [ ] Produce slide-ready content for each section (problem, research, solution, demo, roadmap)

### Out of Scope

- Building new Solidity contracts — this is documentation/presentation work only
- Implementing the CFMM or vault — those are roadmap items to mention, not deliver
- Slide design/formatting tool (Google Slides, Keynote) — we produce content, not slide files
- Research replication or re-running econometric models

## Context

### Research Foundation
- **Econometric identification**: Quadratic deviation exit hazard model on ETH/USDC 30bps pool (41 days, 600 positions, 3,365 position-day observations)
- **Key finding**: Inverted-U relationship — below turning point delta* ~ 0.09, concentration is protective (shelter); above it, concentration drives LP exits (Capponi regime)
- **Backtest**: Power-squared exit payoff (alpha=2) dominates 6 alternatives — 18.8% of positions better off, positive mean hedge value at R0=$200K seed
- **Literature**: Grounded in Capponi & Zhu (exit thresholds), Ma & Crapis (competitive null), Aquilina et al. (empirical validation), Bichuch & Feinstein (fee-as-derivative pricing)

### Solution Architecture (from model)
- **FCI Hook**: Uniswap V4 hook tracking A_T (fee concentration index), ThetaSum (aggregate turnover), N (position count). DeltaPlus derived on the fly.
- **Reactive Adapter**: Cross-protocol integration via Reactive Network — V3 pools emit events that the adapter translates into V4 hook calls
- **CFMM (designed, not implemented)**: Lendgine-style with linearized power-squared trading function psi(u,y) = y - (pL^2/4)u. Underwriters deposit USDC, PLPs borrow LP shares.
- **Vault (designed, not implemented)**: Settlement mechanism for premium collection and payout distribution

### Existing Implementation
- FCI V2 contracts: `src/fee-concentration-index-v2/` — modular, multi-protocol
- Protocol adapters: `src/protocol-adapter/` — Uniswap V3 reactive integration working on Sepolia+Lasna
- Integration tests: `test/fee-concentration-index-v2/protocols/` — native V4 and V3 reactive tests
- Research: `research/` — backtest, econometrics, model (LaTeX), notebooks, 114 Python tests

### Demo Test
- `test/fee-concentration-index-v2/protocols/uniswapV4/NativeV4FeeConcentrationIndex.integration.t.sol` — runs native V4 scenarios showing FCI tracking through swap/mint/burn events

## Constraints

- **Branch**: Work is on `008-uniswap-v3-reactive-integration`
- **Audience**: Mixed (technical + non-technical) — diagrams must be accessible, technical depth in appendix
- **Solidity review rule**: Any Solidity code changes require piece-by-piece user approval (per memory). This task is docs-only so should not apply.
- **Time**: Presentation prep — prioritize clarity and completeness over polish

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Mermaid for diagrams | Renders in README, version-controlled, embeddable in slides | -- Pending |
| Demo = existing integration test | No new code needed, shows real FCI tracking on V4 | -- Pending |
| Roadmap framed as "missing pieces" | Honest about current state, shows clear path forward | -- Pending |
| Adverse competition (not impermanent loss) | Orthogonal risk to LVR — key differentiator from existing hedging products | -- Pending |

---
*Last updated: 2026-03-18 after initialization*
