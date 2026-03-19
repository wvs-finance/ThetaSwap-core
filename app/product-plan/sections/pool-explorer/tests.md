# Pool Explorer Tests

## Rendering Tests

### Table Structure
- [ ] Renders 9 column headers: Pool, Fee, Delta-plus Epoch, Trend, theta-sum, Positions, TVL, 24h Vol, Vault
- [ ] Renders correct number of pool rows from sample data (10 pools)
- [ ] Shows pool count in filter bar (e.g., "10 pools")
- [ ] Empty state shows "No pools match the current filters." when filtered to zero results

### Data Display
- [ ] Pool pair renders as "ETH / USDC" (with separator span)
- [ ] Fee tier renders in basis points: "30bps", "5bps", "100bps"
- [ ] Delta-plus Epoch renders to 2 decimal places: "0.72"
- [ ] TVL renders with suffix: "$487M", "$45M", "$28M", "$1.2M"
- [ ] 24h Volume renders with suffix: "$189M", "$18M", "$380K"
- [ ] theta-sum renders to 2 decimal places: "34.72"
- [ ] Position count renders with locale formatting

### Sparkline
- [ ] Sparkline SVG renders for each pool (80x24 viewport)
- [ ] Sparkline stroke color matches severity of current Delta-plus Epoch
- [ ] Sparkline has area fill at 10% opacity

### Vault Badges
- [ ] Active vault: "Active + Xd" in amber text on amber/15 background
- [ ] Settled vault: "Settled" in slate text on slate/40 background
- [ ] No vault: em-dash in zinc text on zinc-800 background
- [ ] Active vault countdown calculates days from expiry timestamp

### Severity Colors
- [ ] Delta-plus 0.04 (AAVE/ETH) renders in text-slate-400
- [ ] Delta-plus 0.23 (ARB/ETH) renders in text-amber-400
- [ ] Delta-plus 0.55 (MATIC/USDC) renders in text-orange-400
- [ ] Delta-plus 0.84 (CRV/USDC) renders in text-red-400

## Interaction Tests

### Sorting
- [ ] Clicking "Delta-plus Epoch" header sorts descending (default first click)
- [ ] Clicking same header again toggles to ascending
- [ ] Clicking different header resets to descending
- [ ] Active sort column header text is slate-300 (non-active: slate-500)
- [ ] Active sort column shows ChevronUp (asc) or ChevronDown (desc) icon
- [ ] Inactive columns show transparent chevron (preserves alignment)
- [ ] onSort callback fires with (column, direction)

### Filtering
- [ ] Typing "ETH" in search input filters to pools with ETH in either token
- [ ] Fee tier dropdown shows unique values: "All fees", "5bps", "30bps", "100bps"
- [ ] Selecting "5bps" filters to MATIC/USDC and CRV/USDC
- [ ] Vault status "Active" shows only pools with active (non-settled) vaults
- [ ] Vault status "Settled" shows only settled vaults (ARB/ETH, LINK/ETH, CRV/USDC)
- [ ] Vault status "No Vault" shows pools with null vault (OP/ETH, UNI/ETH, AAVE/ETH)
- [ ] Clearing filters restores all 10 pools
- [ ] Pool count updates after filtering
- [ ] onFilter callback fires with current filter state

### Row Click
- [ ] Clicking a pool row fires onPoolClick with the Pool object
- [ ] Rows have cursor-pointer style
- [ ] Row hover applies bg-zinc-800/60

### Tooltip
- [ ] Hovering Delta-plus Epoch column header shows methodology tooltip
- [ ] Tooltip text: "Delta-plus = fee concentration severity. 0 = competitive, 1 = fully extracted."
- [ ] Info icon (12px) visible in header, transitions from slate-600 to slate-400 on hover

## Layout Tests
- [ ] Table has sticky header (stays visible when scrolling)
- [ ] Header has backdrop-blur-sm for translucency
- [ ] Alternating row backgrounds: bg-zinc-900/50 and bg-zinc-950
- [ ] All numeric cells use IBM Plex Mono with tabular-nums
- [ ] Table min-width 1060px (horizontal scroll on narrow viewports)
