# Step 1: Application Shell

## Goal
Build the ThetaSwap application shell -- a collapsible sidebar navigation with top bar, providing the layout frame for all sections.

## Components to Build

### AppShell.tsx
Root layout component with three zones:
- **Left sidebar** (`<aside>`): 240px expanded, 64px collapsed. `bg-zinc-900`, `border-r border-zinc-800`. Contains `<MainNav>`.
- **Top bar** (`<header>`): 48px height. Breadcrumbs on the left (IBM Plex Sans, small text). `<UserMenu>` on the right. `bg-zinc-900`, `border-b border-zinc-800`.
- **Main content** (`<main>`): `flex-1 overflow-auto`. No max-width constraint -- Pool Terminal needs full viewport width.

Body: `bg-zinc-950 text-slate-200`, full viewport (`h-screen w-screen overflow-hidden`).

**Props**: `children`, `currentPath`, `onNavigate`, `breadcrumbs[]`, `sidebarCollapsed`, `onToggleSidebar`, `navigationItems[]`, `walletAddress?`, `network?`, `theme?`, `onConnect?`, `onThemeToggle?`.

### MainNav.tsx
Sidebar navigation with:
- **Logo**: "ThetaSwap" in Instrument Serif italic (collapsed: just "T")
- **Nav items**: Pools (BarChart3), Portfolio (Wallet), Research (BookOpen) -- main section. Settings (Settings) -- bottom, below separator.
- **Active indicator**: amber-500 text + `bg-amber-500/10` background + 3px left amber bar
- **Inactive**: slate-400 text, hover: `bg-zinc-800 text-slate-200`
- **Collapse toggle**: PanelLeftClose / PanelLeftOpen icon at bottom

**Props**: `items: NavItem[]`, `activeItem: string`, `onItemClick`, `collapsed`, `onToggleCollapse`.

### UserMenu.tsx
Top bar right section:
- **Network indicator**: Small green dot + network name in `bg-zinc-800` pill
- **Wallet button**: Connected = truncated address (0x1234...abcd), border hover -> amber. Disconnected = "Connect Wallet" button.
- **Theme toggle**: Sun/Moon icon button

**Props**: `walletAddress?`, `network?`, `theme?`, `onConnect?`, `onThemeToggle?`.

## Icons Required (lucide-react)
`BarChart3`, `Wallet`, `BookOpen`, `Settings`, `PanelLeftClose`, `PanelLeftOpen`, `Sun`, `Moon`

## Default Navigation Items
```typescript
const navItems: NavItem[] = [
  { id: 'pools', label: 'Pools', href: '/', icon: 'pools' },
  { id: 'portfolio', label: 'Portfolio', href: '/portfolio', icon: 'portfolio' },
  { id: 'research', label: 'Research', href: '/research', icon: 'research' },
  { id: 'settings', label: 'Settings', href: '/settings', icon: 'settings' },
]
```

## Verification
- Sidebar expands/collapses smoothly (200ms transition)
- Active nav item is highlighted when path matches
- Breadcrumbs render with `/` separators
- Network dot is emerald-500
- Theme toggle switches Sun/Moon icons
