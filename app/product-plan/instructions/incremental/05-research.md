# Step 5: Research

## Goal
Build the Research section -- an academic-style backtest report. This section DELIBERATELY breaks from the terminal aesthetic to present findings as a readable article.

## Dependencies
```bash
npm install katex
npm install -D @types/katex
```
Import `katex/dist/katex.min.css` in the component.

## Layout
Single-column article, `max-w-[960px] mx-auto`, generous padding (px-8 py-10). Body font: IBM Plex Sans. Headings: Instrument Serif italic.

## Component: Research.tsx

### Tex Sub-component
Inline LaTeX renderer using `katex.render()`:
```typescript
function Tex({ math, display = false }: { math: string; display?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    if (ref.current) {
      katex.render(math, ref.current, { displayMode: display, throwOnError: false, trust: true })
    }
  }, [math, display])
  return <span ref={ref} />
}
```

### Section 1: Abstract
- Title: Instrument Serif, 3xl italic
- Subtitle: "ThetaSwap Research -- Backtest Report -- ETH-USDC 30bps" in zinc-500
- Horizontal rule
- Abstract paragraph referencing Delta-plus (rendered as LaTeX `\Delta^+`)
- 3 summary stat cards: "Epochs Above Strike" (121/180), "% Better Off Hedged" (67.2%), "Mean Hedge Value" ($0.034/$1)

### Section 2: Methodology
Numbered "section-2" with subsections:
- **Data Source**: Description text
- **Mechanism**: Explains epoch-based Delta-plus accumulation with inline LaTeX formulas (Theta, A_T, Delta-plus)
- **Payoff Function**: Description + display-mode formula in bordered box:
  ```
  p(HWM, K) = max(0, ((HWM - K)/(1 - K))^2)
  ```

### Section 3: Results (3 SVG Charts)

**Figure 1: Welfare Bar Chart** (~480x200 viewport)
- Bars: Unhedged (red), Hedged K=0.15 (amber), Hedged K=0.25 (amber), Hedged K=0.35 (amber)
- Y-axis: Welfare (Delta fee revenue)
- Error bars: +/- 1 std dev with cap lines
- Zero line

**Figure 2: Delta-plus Distribution Histogram** (~480x180 viewport)
- 10 bins from 0.0-0.1 through 0.9-1.0
- Bar colors gradient: low bins = zinc, mid = amber, high = orange/red
- Count labels above bars
- X-axis: "Delta-plus Range", Y-axis: "Epoch Count"

**Figure 3: Payoff Sensitivity Line Chart** (~480x180 viewport)
- Line with data points showing mean payout vs strike
- Area fill (amber, 6% opacity)
- Vertical dashed line at K=0.25 (default strike)
- X-axis: "Strike (K)", Y-axis: "Mean Payout"

Each chart wrapped in `border border-zinc-800 bg-zinc-900/50 p-4` with figure caption and description.

### Section 4: Calibration Parameters
Table with 3 columns: Parameter (LaTeX-rendered name in amber), Value (monospace), Description.
Parameters: gamma, alpha, epochLength, K (strike), atNull_0.
LaTeX parameter names mapped via lookup table.
Footer note about conservation: p_LONG + p_SHORT = 1.

### Section 5: Conclusion
Final paragraph discussing when insurance is valuable (Delta-plus > 0.20, epoch lengths 1-7 days).

### Footer
Disclaimer: "This report is auto-generated from backtest data. It does not constitute financial advice."

## Verification
- LaTeX formulas render correctly (Delta-plus, theta, payoff formula)
- Display-mode formula is centered in a bordered box
- Welfare chart shows negative values with bars extending below zero line
- Distribution histogram bars colored by severity gradient
- Sensitivity chart has K=0.25 dashed reference line
- Parameter table renders LaTeX symbols (gamma, alpha) in amber
- Article layout is centered at max 960px (unlike full-width terminal sections)
- Dark mode with paper-like content area aesthetic
