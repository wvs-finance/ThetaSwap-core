# Pool Explorer

## Overview

Discovery and comparison of all monitored Uniswap V4 pools. A dense, sortable, filterable table showing real-time fee concentration metrics, vault status, and pool fundamentals. The primary entry point — users scan for pools with high JIT concentration risk before drilling into the Pool Terminal.

## User Flows

1. **Scan and sort** — Sort table by Δ⁺ (fee concentration) to identify pools with high JIT extraction risk
2. **Filter** — Narrow by token pair, fee tier, or vault status (Active / Settled / No Vault)
3. **Drill down** — Click any pool row to navigate to the Pool Terminal for a full deep dive

## UI Requirements

### Table Columns
- **Pool Pair** — Token symbols with small icons (e.g., ETH / USDC)
- **Fee Tier** — Pool fee in basis points (e.g., 30bps)
- **Δ⁺ (Epoch)** — Current epoch-reset fee concentration (from getDeltaPlusEpoch). Primary metric. Severity-colored: < 0.2 muted zinc, 0.2–0.5 amber, 0.5–0.8 orange, > 0.8 red
- **Δ⁺ Trend** — Inline sparkline (tiny area chart) of last 24 epoch readings
- **θ-sum** — Cumulative theta sum (Σ(1/ℓ_k))
- **Positions** — Active position count (mock static value)
- **TVL** — Total value locked in USD (mock static value)
- **24h Volume** — Trading volume in USD (mock static value)
- **Vault** — Status badge: "Active" (with expiry countdown), "Settled", or "No Vault"

### Interactions
- Click column headers to sort (ascending/descending toggle)
- Filter controls above table (dropdowns or input fields)
- Click row to navigate to Pool Terminal
- Hover Δ⁺ column header shows methodology tooltip: "Δ⁺ = fee concentration severity. 0 = competitive, 1 = fully extracted. Derived from Σ(1/ℓ_k) over position removals."

### Design Notes
- No cards, no grid. Dense sortable table only.
- All numeric values in IBM Plex Mono (monospace)
- Headings in IBM Plex Sans
- Dark mode primary (zinc-950 background, zinc-900 table rows)
- Alternating row backgrounds for scanability (zinc-900 / zinc-950)
- Compact row height (40-44px) for data density

## Configuration
- shell: false
