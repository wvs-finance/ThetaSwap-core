# Shell

Application shell providing the layout frame for all ThetaSwap sections.

## Structure

- **Left Sidebar** (240px expanded, 64px collapsed): Logo, navigation, settings, collapse toggle
- **Top Bar** (48px): Breadcrumbs, wallet connect, network indicator, theme toggle
- **Main Content Area**: Fills remaining viewport, no max-width constraint

## Components

| Component | Description |
|-----------|-------------|
| `AppShell` | Root layout: sidebar + topbar + content slot |
| `MainNav` | Sidebar navigation with collapse state |
| `UserMenu` | Wallet button, network dot, theme toggle |

## Navigation Items

| Label | Icon | Route | Description |
|-------|------|-------|-------------|
| Pools | BarChart3 | `/` | Pool Explorer (default landing page) |
| Portfolio | Wallet | `/portfolio` | User's LONG/SHORT positions |
| Research | BookOpen | `/research` | Backtest results report |
| Settings | Settings | `/settings` | Theme, RPC configuration |

## Key Behaviors

- Pool Explorer is the landing page
- Clicking a pool row navigates to Pool Terminal -- sidebar still highlights "Pools"
- Sidebar collapse preserves icon-only view (64px) for maximum content width
- Dark mode is the default theme
- Network indicator shows a green (emerald-500) dot when connected

## Dependencies

- `lucide-react`: BarChart3, Wallet, BookOpen, Settings, PanelLeftClose, PanelLeftOpen, Sun, Moon
