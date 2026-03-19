# Application Shell Specification

## Layout Pattern

Sidebar Navigation (collapsible)

## Structure

### Left Sidebar (240px, collapsible to 64px icon-only)

- **Logo/Wordmark**: "ThetaSwap" in Instrument Serif, small
- **Navigation Items**:
  1. **Pools** — Pool Explorer (default/home view)
  2. **Portfolio** — User's positions and balances
  3. **Research** — Backtest results and methodology
- **Separator**
- **Settings** (bottom) — Theme toggle, RPC configuration

No user menu or avatar in the sidebar.

### Top Bar (48px, minimal)

- **Left**: Breadcrumb showing current location (e.g., `Pools / ETH-USDC / Terminal`)
- **Right**: Wallet connect button, network indicator, dark/light theme toggle

### Main Content Area

Fills remaining viewport space. **No max-width constraint** — the Pool Terminal's three-pane layout needs full viewport width.

## Navigation Behavior

- Pool Explorer is the landing page (default route)
- Clicking a pool row in the explorer navigates to Pool Terminal (drill-down)
- Pool Terminal is NOT a separate nav item — sidebar highlights "Pools" for both explorer and terminal views
- Collapsible sidebar lets users reclaim horizontal space when in terminal view

## Responsive Behavior

- Desktop-first design
- Sidebar collapses to icon-only (64px) via toggle button
- On mobile viewports, sidebar becomes a hamburger menu overlay

## Design Tokens Applied

- Colors: slate (primary), amber (secondary), zinc (neutral)
- Typography: Instrument Serif (logo/headings), IBM Plex Sans (nav labels), IBM Plex Mono (not used in shell)
- Dark mode is the default theme
