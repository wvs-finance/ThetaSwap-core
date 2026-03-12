import React, { useState } from 'react'
import { AppShell } from './components/AppShell'
import type { NavItem } from './components/MainNav'
import type { Breadcrumb } from './components/AppShell'

const navigationItems: NavItem[] = [
  { id: 'pools', label: 'Pools', href: '/pools', icon: 'pools' },
  { id: 'portfolio', label: 'Portfolio', href: '/portfolio', icon: 'portfolio' },
  { id: 'research', label: 'Research', href: '/research', icon: 'research' },
  { id: 'settings', label: 'Settings', href: '/settings', icon: 'settings' },
]

export default function ShellPreview() {
  const [currentPath, setCurrentPath] = useState('/pools')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')

  const breadcrumbs: Breadcrumb[] = [
    { label: 'Pools', href: '/pools' },
  ]

  return (
    <AppShell
      currentPath={currentPath}
      onNavigate={(href) => {
        setCurrentPath(href)
        console.log('Navigate to:', href)
      }}
      breadcrumbs={breadcrumbs}
      sidebarCollapsed={sidebarCollapsed}
      onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
      navigationItems={navigationItems}
      network="Mainnet"
      theme={theme}
      onConnect={() => console.log('Connect wallet')}
      onThemeToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
    >
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h1 className="mb-2 text-2xl font-semibold text-slate-200 font-[family-name:'Instrument_Serif']">
            Pool Explorer
          </h1>
          <p className="text-sm text-slate-500 font-[family-name:'IBM_Plex_Sans']">
            Section content will render here.
          </p>
        </div>
      </div>
    </AppShell>
  )
}
