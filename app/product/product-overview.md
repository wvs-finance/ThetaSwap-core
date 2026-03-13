# ThetaSwap

## Description
Insurance protocol for passive liquidity providers hedging against just-in-time liquidity extraction on Uniswap V4. ThetaSwap quantifies fee concentration risk with an on-chain oracle and offers paired LONG/SHORT tokens that settle based on observed severity.

## Problems & Solutions

### Problem 1: JIT Fee Extraction
Passive LPs on Uniswap lose fee revenue to JIT snipers who front-run swaps with concentrated, short-lived positions.

Fee Concentration Index (Δ⁺) — an on-chain oracle measuring fee concentration severity per pool, ranging from 0 (competitive) to 1 (fully extracted). Provides the first quantitative signal for JIT risk.

### Problem 2: No On-Chain Concentration Metric
No on-chain metric exists to quantify how much fee revenue is being extracted by JIT competition, leaving LPs blind to the magnitude of the problem.

Δ⁺ is derived from position-level HHI-weighted fee shares and sophistication weights (1/block_lifetime), computed at every liquidity removal. The competitive null (atNull) establishes a baseline so the deviation captures only excess concentration.

### Problem 3: No Hedging Instrument
LPs have no hedging instrument — they either accept the loss or stop providing liquidity entirely.

LONG/SHORT token vault — deposit USDC, receive paired tokens. LONG pays out when Δ⁺ exceeds the strike (insurance). SHORT is the counterparty. Oracle-based settlement uses a lookback payoff where HWM captures the worst concentration observed, and a power-squared formula rewards hedgers proportionally to tail severity.

## Key Features
- Live pool monitoring with severity indicators and epoch-reset Δ⁺ sparklines
- Vault deposit and redeem with paired LONG + SHORT minting (ERC-6909)
- Payoff curve visualization showing LONG payout as a function of Δ⁺
- Academic-style backtest research reports with hedged vs. unhedged welfare comparisons
