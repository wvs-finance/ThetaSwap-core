# Research Tests

## Layout

- [ ] Article container: max-w-[960px] mx-auto centered
- [ ] Body padding: px-8 py-10
- [ ] Base font: IBM Plex Sans
- [ ] Background: bg-zinc-950 (same as app, but content area feels article-like)
- [ ] NOT full-width like Pool Explorer/Terminal -- deliberately constrained

## Section 1: Abstract

### Title
- [ ] Title renders in Instrument Serif, 3xl, italic: "Insurance Backtest: ETH-USDC Liquidity Provider Hedging"
- [ ] Subtitle: "ThetaSwap Research -- Backtest Report -- ETH-USDC 30bps" in zinc-500
- [ ] Horizontal rule below subtitle (border-zinc-800)

### Content
- [ ] Abstract paragraph contains inline LaTeX: Delta-plus renders as mathematical symbol
- [ ] KaTeX renders without errors (throwOnError: false)

### Summary Stat Cards
- [ ] 3 cards in a grid-cols-3 layout
- [ ] "Epochs Above Strike" shows "121 / 180"
- [ ] "% Better Off Hedged" shows "67.2%"
- [ ] "Mean Hedge Value" shows "$0.034 / $1"
- [ ] Cards: border border-zinc-800 bg-zinc-900 rounded-none

## Section 2: Methodology

- [ ] Section number "S2" in IBM Plex Mono, zinc-500
- [ ] "Methodology" heading in Instrument Serif italic
- [ ] Three subsections: Data Source, Mechanism, Payoff Function
- [ ] Subsection headers: text-sm font-medium uppercase tracking-wider text-zinc-500
- [ ] Mechanism text contains inline LaTeX: Theta, A_T, Delta-plus formulas
- [ ] Display-mode formula in bordered box: p(HWM, K) = max(0, ((HWM - K)/(1 - K))^2)
- [ ] Formula box: border border-zinc-800 bg-zinc-900 rounded-none, centered text

## Section 3: Results

### Figure 1: Welfare Bar Chart
- [ ] Caption: "Figure 1. Hedged vs Unhedged LP Welfare"
- [ ] Description: "Mean change in fee revenue per dollar of liquidity. Error bars: +/-1 std dev."
- [ ] Chart container: border border-zinc-800 bg-zinc-900/50 p-4
- [ ] 4 bars: "Unhedged" (red), "Hedged (K=0.15)" (amber), "Hedged (K=0.25)" (amber), "Hedged (K=0.35)" (amber)
- [ ] Error bars with cap lines (+/- 1 std dev)
- [ ] Zero line visible
- [ ] Y-axis label: "Welfare (Delta fee revenue)"
- [ ] X-axis labels: bar names in IBM Plex Mono

### Figure 2: Delta-plus Distribution
- [ ] Caption: "Figure 2. Delta-plus Distribution Across Epochs"
- [ ] 10 histogram bins from 0.0-0.1 through 0.9-1.0
- [ ] Bar colors gradient: low = zinc (#71717a), mid = amber (#fbbf24), high = orange/red (#fb923c, #f87171)
- [ ] Count labels above each bar
- [ ] X-axis: "Delta-plus Range", Y-axis: "Epoch Count"

### Figure 3: Payoff Sensitivity
- [ ] Caption: "Figure 3. Payoff Sensitivity to Strike"
- [ ] Line chart with data points (circles)
- [ ] Amber line (#fbbf24) with area fill (6% opacity)
- [ ] Vertical dashed reference line at K=0.25 with "K=0.25" label
- [ ] X-axis: "Strike (K)", Y-axis: "Mean Payout"
- [ ] X labels at alternating strike values

## Section 4: Calibration Parameters

- [ ] Section number "S4" in IBM Plex Mono
- [ ] "Calibration Parameters" heading
- [ ] Table with 3 columns: Parameter, Value, Description
- [ ] Parameter column headers: text-xs font-medium uppercase tracking-wider text-slate-500
- [ ] Parameter names rendered as LaTeX (amber text): gamma, alpha, epochLength, K, atNull_0
- [ ] Values in IBM Plex Mono, right-aligned, tabular-nums
- [ ] Footer note: "Conservation: p_LONG + p_SHORT = 1 per token pair" (with LaTeX)
- [ ] Alternating row backgrounds

## Section 5: Conclusion

- [ ] Section number "S5" in IBM Plex Mono
- [ ] "Conclusion" heading in Instrument Serif italic
- [ ] Paragraph with inline LaTeX: Delta-plus > 0.20, K = 0.25, K = 0.15
- [ ] Text about when insurance is valuable

## Footer

- [ ] Horizontal rule (border-zinc-800)
- [ ] Disclaimer in zinc-600, text-xs
- [ ] "This report is auto-generated from backtest data. It does not constitute financial advice."

## KaTeX Integration

- [ ] katex package imported
- [ ] katex/dist/katex.min.css imported
- [ ] Tex component uses useRef + useEffect with katex.render()
- [ ] Display mode formulas render centered and larger
- [ ] Inline formulas render within text flow
- [ ] throwOnError: false prevents crashes on malformed LaTeX
