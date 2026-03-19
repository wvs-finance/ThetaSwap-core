# Research

Pre-rendered backtest results styled as an academic research report. Builds trust before users deposit. DELIBERATELY DIFFERENT from the terminal aesthetic -- this is an article, not a dashboard.

## Layout

Single-column, article-style. Max-width 960px centered. Generous margins. Instrument Serif headings. Numbered sections.

## Content Sections

1. **Abstract** -- One paragraph summarizing backtest findings + 3 summary stat cards
2. **Methodology** -- Data source, mechanism description, payoff formula (KaTeX display mode)
3. **Results** -- 3 SVG charts: welfare bar chart, Delta-plus distribution histogram, payoff sensitivity line chart
4. **Parameters** -- Table of calibrated values with LaTeX-rendered parameter names
5. **Conclusion** -- When insurance is valuable

## Charts (all SVG, no chart libraries)

| Chart | Type | Description |
|-------|------|-------------|
| Welfare Comparison | Bar chart | Hedged vs unhedged LP welfare with error bars |
| Delta-plus Distribution | Histogram | Epoch-maximum Delta-plus frequency, severity-colored |
| Payoff Sensitivity | Line chart | Mean LONG payout vs strike K |

## Dependencies

- `katex` -- LaTeX formula rendering (inline and display mode)
- `katex/dist/katex.min.css` -- KaTeX stylesheet
- `lucide-react` -- Not used in this section

## Important Notes

- This section uses `useRef` + `useEffect` for KaTeX rendering
- The Tex component renders LaTeX math via `katex.render()` with `throwOnError: false`
- Parameter names (gamma, alpha, etc.) are rendered as LaTeX symbols via a lookup table
- The article aesthetic deliberately breaks from the dense terminal look of other sections
