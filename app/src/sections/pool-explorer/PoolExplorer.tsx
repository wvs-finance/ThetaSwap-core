import { useState } from 'react'
import { PoolExplorer as PoolExplorerComponent } from './components/PoolExplorer'
import data from '@/../product/sections/pool-explorer/data.json'
import { AppShell } from '../../shell/components'
import type { NavItem } from '../../shell/components/MainNav'

const navigationItems: NavItem[] = [
  { id: 'pools', label: 'Pools', href: '/pools', icon: 'pools' },
  { id: 'portfolio', label: 'Portfolio', href: '/portfolio', icon: 'portfolio' },
  { id: 'research', label: 'Research', href: '/research', icon: 'research' },
]

export default function PoolExplorerPreview() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <>
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Instrument+Serif&display=swap"
      />
      <AppShell
        currentPath="/pools"
        onNavigate={(href) => console.log('Navigate:', href)}
        breadcrumbs={[{ label: 'Pools' }]}
        sidebarCollapsed={sidebarCollapsed}
        onToggleSidebar={() => setSidebarCollapsed((c) => !c)}
        navigationItems={navigationItems}
        walletAddress="0xe692...47C3"
        network="Mainnet"
        theme="dark"
        onConnect={() => console.log('Connect wallet')}
        onThemeToggle={() => console.log('Toggle theme')}
      >
        <PoolExplorerComponent
          pools={data.pools as any}
          onPoolClick={(pool) =>
            console.log('Navigate to pool:', pool.pair.join('/'))
          }
          onSort={(col, dir) => console.log('Sort:', col, dir)}
          onFilter={(filters) => console.log('Filter:', filters)}
        />
      </AppShell>
    </>
  )
}
