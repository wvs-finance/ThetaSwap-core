# Step 2: Pool Explorer

## Goal
Build the Pool Explorer -- a dense, sortable, filterable table of monitored Uniswap V4 pools with severity-colored Delta-plus values, inline sparklines, and vault status badges.

## Component: PoolExplorer.tsx

### Filter Bar
Top of the component, `border-b border-zinc-800`:
- **Search pair**: Text input, placeholder "Search pair...", filters by token symbol match
- **Fee tier dropdown**: "All fees" default, populated from unique fee tiers in data
- **Vault status dropdown**: "All vaults" / "Active" / "Settled" / "No Vault"
- **Pool count**: Right-aligned, monospace, e.g. "10 pools"

### Table Columns (9 columns)
1. **Pool** (sortable, left-aligned): Token pair "ETH / USDC" in IBM Plex Sans
2. **Fee** (sortable, right): Fee tier in basis points, e.g. "30bps"
3. **Delta-plus Epoch** (sortable, right): Severity-colored value to 2 decimal places. Tooltip on header: "Delta-plus = fee concentration severity. 0 = competitive, 1 = fully extracted."
4. **Trend** (non-sortable): Inline SVG sparkline (80x24px) showing last 24 epoch readings. Stroke color matches severity.
5. **theta-sum** (sortable, right): 2 decimal places
6. **Positions** (sortable, right): Integer count
7. **TVL** (sortable, right): Formatted as $487M, $45M, etc.
8. **24h Vol** (sortable, right): Same formatting as TVL
9. **Vault** (sortable): Badge -- "Active + Xd" (amber bg), "Settled" (slate bg), or em-dash (zinc bg)

### Severity Color Scale
```typescript
function getSeverityColor(delta: number): string {
  if (delta > 0.8) return 'text-red-400'
  if (delta > 0.5) return 'text-orange-400'
  if (delta >= 0.2) return 'text-amber-400'
  return 'text-slate-400'
}
```

### Sorting
- Click column header toggles direction (desc default for first click)
- Active column header: slate-300 text with ChevronUp/ChevronDown icon
- Inactive headers: slate-500 text with transparent chevron (preserves alignment)

### Table Styling
- Sticky header: `bg-zinc-900/95 backdrop-blur-sm`
- Alternating rows: `bg-zinc-900/50` / `bg-zinc-950`
- Row hover: `bg-zinc-800/60`
- Row click: fires `onPoolClick(pool)`
- All column headers: `text-xs font-medium uppercase tracking-wider` in IBM Plex Sans
- All numeric cells: `font-[family-name:'IBM_Plex_Mono'] tabular-nums`

### Sparkline Sub-component
Tiny SVG area chart (80x24px):
- Polyline stroke (1.5px) colored by current Delta-plus severity
- Area fill at 10% opacity
- Min/max scaling within the sparkline data range

## Types
See `types.ts` for Pool, PoolVault, PoolExplorerProps, PoolFilters interfaces.

## Verification
- Sort by Delta-plus descending -- CRV/USDC (0.84) should be first
- Filter by "ETH" -- shows ETH/USDC, WBTC/ETH, ARB/ETH, etc.
- Filter vault status "Active" -- shows only pools with active vaults
- Sparklines render with correct severity colors
- Vault badges show days until expiry for active vaults
- Empty state: "No pools match the current filters."
