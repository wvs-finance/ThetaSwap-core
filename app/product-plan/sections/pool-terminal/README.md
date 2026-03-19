# Pool Terminal

Deep dive into a single pool. All data visible in one dense, terminal-like view. Three-pane split layout showing LP positions, oracle/vault state, payoff curve, and time-series charts. Users arrive here after clicking a pool row in the Pool Explorer.

## Layout

```
+---------------------------+---------------------------+
|   LEFT PANE (45%)         |   RIGHT PANE (55%)        |
|   Position Table          |   Oracle State            |
|   - Sortable columns      |   Vault Controls          |
|   - Expandable rows       |   Payoff Curve (SVG)      |
+-----------------------------------------------------------+
|   BOTTOM STRIP (20% height, min 120px)                    |
|   Delta-plus + HWM Time Series (SVG)                      |
+-----------------------------------------------------------+
```

## Panes

### Left Pane: Position Table
- Columns: Address, Tick Range, Liquidity, Fees (USDC), Blocks, Max Delta-plus
- User positions highlighted with amber left border
- Row click expands inline accordion with position detail

### Right Pane: Oracle + Vault + Payoff
1. **Oracle State**: Large Delta-plus Epoch, secondary metrics, epoch progress bar
2. **Vault**: Strike, HWM, expiry, deposits. Action buttons for deposit/redeem/poke
3. **Payoff Curve**: SVG showing LONG payout vs Delta-plus with strike and HWM markers

### Bottom Strip: Time Series
- Delta-plus line (amber) + HWM line (slate dashed)
- Epoch boundaries as vertical dashed lines
- Time range selector: 1D / 7D / 30D / All

## Key Interactions

| Action | Button Label | Condition |
|--------|-------------|-----------|
| Deposit USDC | "Deposit" | Vault not settled |
| Redeem LONG+SHORT pair | "Redeem Pair" | Vault not settled |
| Update oracle HWM | "Poke" | Vault not settled |
| Redeem LONG tokens | "Redeem LONG" | Vault settled |
| Redeem SHORT tokens | "Redeem SHORT" | Vault settled |

## Dependencies

- `lucide-react`: ChevronUp, ChevronDown, Info, ChevronRight
