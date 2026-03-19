import React from 'react'
import { MainNav, type NavItem } from './MainNav'
import { UserMenu } from './UserMenu'

export interface Breadcrumb {
  label: string
  href?: string
}

export interface AppShellProps {
  children?: React.ReactNode
  currentPath?: string
  onNavigate?: (href: string) => void
  breadcrumbs?: Breadcrumb[]
  sidebarCollapsed?: boolean
  onToggleSidebar?: () => void
  navigationItems?: NavItem[]
  walletAddress?: string
  network?: string
  theme?: 'dark' | 'light'
  onConnect?: () => void
  onThemeToggle?: () => void
}

export function AppShell({
  children,
  currentPath = '/',
  onNavigate = () => {},
  breadcrumbs = [],
  sidebarCollapsed = false,
  onToggleSidebar = () => {},
  navigationItems = [],
  walletAddress,
  network = 'Mainnet',
  theme = 'dark',
  onConnect,
  onThemeToggle,
}: AppShellProps) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-zinc-950 text-slate-200">
      {/* Left Sidebar */}
      <aside
        className={`flex-shrink-0 flex flex-col border-r border-zinc-800 bg-zinc-900 transition-all duration-200 ease-in-out ${
          sidebarCollapsed ? 'w-16' : 'w-60'
        }`}
      >
        <MainNav
          items={navigationItems}
          activeItem={currentPath}
          onItemClick={onNavigate}
          collapsed={sidebarCollapsed}
          onToggleCollapse={onToggleSidebar}
        />
      </aside>

      {/* Main Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="flex h-12 flex-shrink-0 items-center justify-between border-b border-zinc-800 bg-zinc-900 px-4">
          {/* Breadcrumbs */}
          <nav className="flex items-center gap-1.5 text-sm font-[family-name:'IBM_Plex_Sans']">
            {breadcrumbs.map((crumb, i) => (
              <React.Fragment key={i}>
                {i > 0 && <span className="text-zinc-600">/</span>}
                {crumb.href ? (
                  <button
                    onClick={() => onNavigate(crumb.href!)}
                    className="text-slate-400 transition-colors duration-200 hover:text-slate-200"
                  >
                    {crumb.label}
                  </button>
                ) : (
                  <span className="text-slate-400">{crumb.label}</span>
                )}
              </React.Fragment>
            ))}
          </nav>

          {/* Right Section */}
          <UserMenu
            walletAddress={walletAddress}
            network={network}
            theme={theme}
            onConnect={onConnect}
            onThemeToggle={onThemeToggle}
          />
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  )
}
