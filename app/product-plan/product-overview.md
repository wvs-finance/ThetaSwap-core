# ThetaSwap

## Description
Insurance protocol for passive liquidity providers hedging against just-in-time liquidity extraction on Uniswap V4. ThetaSwap quantifies fee concentration risk with an on-chain oracle and offers paired LONG/SHORT tokens that settle based on observed severity.

## Problems & Solutions

### Problem 1: JIT Fee Extraction
Passive LPs on Uniswap lose fee revenue to JIT snipers who front-run swaps with concentrated, short-lived positions.

Fee Concentration Index (Delta-plus) -- an on-chain oracle measuring fee concentration severity per pool, ranging from 0 (competitive) to 1 (fully extracted). Provides the first quantitative signal for JIT risk.

### Problem 2: No On-Chain Concentration Metric
No on-chain metric exists to quantify how much fee revenue is being extracted by JIT competition, leaving LPs blind to the magnitude of the problem.

Delta-plus is derived from position-level HHI-weighted fee shares and sophistication weights (1/block_lifetime), computed at every liquidity removal. The competitive null (atNull) establishes a baseline so the deviation captures only excess concentration.

### Problem 3: No Hedging Instrument
LPs have no hedging instrument -- they either accept the loss or stop providing liquidity entirely.

LONG/SHORT token vault -- deposit USDC, receive paired tokens. LONG pays out when Delta-plus exceeds the strike (insurance). SHORT is the counterparty. Oracle-based settlement uses a lookback payoff where HWM captures the worst concentration observed, and a power-squared formula rewards hedgers proportionally to tail severity.

## Key Features
- Live pool monitoring with severity indicators and epoch-reset Delta-plus sparklines
- Vault deposit and redeem with paired LONG + SHORT minting (ERC-6909)
- Payoff curve visualization showing LONG payout as a function of Delta-plus
- Academic-style backtest research reports with hedged vs. unhedged welfare comparisons

## Sections

### 1. Pool Explorer
Discovery and comparison of all monitored pools. A dense, sortable table showing current Delta-plus (fee concentration severity), sparklines, theta-sum, TVL, and vault status for each pool. The front door of the application -- users scan, sort, and filter to find pools with high concentration risk before drilling into details.

### 2. Pool Terminal
Deep dive into a single pool. A three-pane split layout: positions table (left), oracle state + vault operations + payoff curve (right), and time-series charts (bottom). All data visible at once -- no tab switching. This is the core experience where users monitor concentration risk, reference the payoff curve, and execute vault operations.

### 3. Portfolio
User's aggregate LONG/SHORT positions across all vaults. Summary strip showing total USDC deposited, LONG and SHORT token values, and net P&L. Active vault table with payout previews, plus a settled vaults history section showing realized results -- the "was hedging worth it?" evidence.

### 4. Research
Pre-rendered backtest results styled as an academic research report. Abstract, methodology, results charts (hedged vs unhedged welfare, Delta-plus distributions, payoff sensitivity), calibrated parameters, and conclusions. Builds trust with quantitative users before they deposit. Deliberately breaks from the terminal aesthetic -- article-style, max-width 960px, Instrument Serif headings.
