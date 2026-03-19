# Pool Explorer

Discovery and comparison of all monitored Uniswap V4 pools. A dense, sortable, filterable table showing real-time fee concentration metrics, vault status, and pool fundamentals. The primary entry point -- users scan for pools with high JIT concentration risk before drilling into the Pool Terminal.

## User Flows

1. **Scan and sort** -- Sort table by Delta-plus (fee concentration) to identify pools with high JIT extraction risk
2. **Filter** -- Narrow by token pair, fee tier, or vault status (Active / Settled / No Vault)
3. **Drill down** -- Click any pool row to navigate to the Pool Terminal for a full deep dive

## Table Columns

| Column | Sortable | Alignment | Font | Notes |
|--------|----------|-----------|------|-------|
| Pool Pair | Yes | Left | IBM Plex Sans | "ETH / USDC" |
| Fee | Yes | Right | IBM Plex Mono | "30bps" |
| Delta-plus Epoch | Yes | Right | IBM Plex Mono | Severity-colored |
| Trend | No | Left | -- | Inline SVG sparkline (80x24px) |
| theta-sum | Yes | Right | IBM Plex Mono | Cumulative sum |
| Positions | Yes | Right | IBM Plex Mono | Active count |
| TVL | Yes | Right | IBM Plex Mono | "$487M" format |
| 24h Vol | Yes | Right | IBM Plex Mono | "$189M" format |
| Vault | Yes | Left | IBM Plex Mono | Status badge |

## Severity Color Scale

| Delta-plus Range | Text Class | Stroke Hex |
|-----------------|------------|------------|
| < 0.2 | text-slate-400 | #94a3b8 |
| 0.2 - 0.5 | text-amber-400 | #fbbf24 |
| 0.5 - 0.8 | text-orange-400 | #fb923c |
| > 0.8 | text-red-400 | #f87171 |

## Dependencies

- `lucide-react`: ChevronUp, ChevronDown, Info
