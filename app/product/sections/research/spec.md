# Research

## Overview

Pre-rendered backtest results styled as an academic research report. Builds trust before users deposit. DELIBERATELY DIFFERENT from the terminal aesthetic -- this is an article, not a dashboard.

## Layout

Single-column, article-style. Max-width 960px centered. Generous margins. Instrument Serif headings. Numbered sections.

## Content Sections

1. **Abstract** -- One paragraph summarizing backtest findings
2. **Methodology** -- Data source, mechanism, payoff formula
3. **Results** -- Summary statistics + 3 charts (welfare comparison, Δ⁺ distribution, payoff sensitivity)
4. **Parameters** -- Table of calibrated values with descriptions
5. **Conclusion** -- When insurance is valuable

## Design Notes
- Styled like an academic paper, not a dashboard
- Charts are static SVG (bar chart, histogram, line chart)
- Formula notation inline in IBM Plex Mono
- Citation-style references
- Dark mode works but with paper-like content area

## Configuration
- shell: false
