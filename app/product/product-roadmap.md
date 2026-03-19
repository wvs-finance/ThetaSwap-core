# Product Roadmap

### 1. Pool Explorer

Discovery and comparison of all monitored pools. A dense, sortable table showing current Δ⁺ (fee concentration severity), sparklines, theta-sum, TVL, and vault status for each pool. The front door of the application — users scan, sort, and filter to find pools with high concentration risk before drilling into details.

### 2. Pool Terminal

Deep dive into a single pool. A three-pane split layout: positions table (left), oracle state + vault operations + payoff curve (right), and time-series charts (bottom). All data visible at once — no tab switching. This is the core experience where users monitor concentration risk, reference the payoff curve, and execute vault operations.

### 3. Portfolio

User's aggregate LONG/SHORT positions across all vaults. Summary strip showing total USDC deposited, LONG and SHORT token values, and net P&L. Active vault table with payout previews, plus a settled vaults history section showing realized results — the "was hedging worth it?" evidence.

### 4. Research

Pre-rendered backtest results styled as an academic research report. Abstract, methodology, results charts (hedged vs unhedged welfare, Δ⁺ distributions, payoff sensitivity), calibrated parameters, and conclusions. Builds trust with quantitative users before they deposit. Deliberately breaks from the terminal aesthetic — article-style, max-width 960px, Instrument Serif headings.
