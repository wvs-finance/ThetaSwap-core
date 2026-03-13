import { useState } from 'react'
import { Portfolio as PortfolioComponent } from './components/Portfolio'
import data from '@/../product/sections/portfolio/data.json'
import { AppShell } from '../../shell/components'
import type { NavItem } from '../../shell/components/MainNav'

const navigationItems: NavItem[] = [
  { id: 'pools', label: 'Pools', href: '/pools', icon: 'pools' },
  { id: 'portfolio', label: 'Portfolio', href: '/portfolio', icon: 'portfolio' },
  { id: 'research', label: 'Research', href: '/research', icon: 'research' },
]

export default function PortfolioPreview() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <>
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Instrument+Serif&display=swap"
      />
      <AppShell
        currentPath="/portfolio"
        onNavigate={(href) => console.log('Navigate:', href)}
        breadcrumbs={[{ label: 'Portfolio' }]}
        sidebarCollapsed={sidebarCollapsed}
        onToggleSidebar={() => setSidebarCollapsed((c) => !c)}
        navigationItems={navigationItems}
        walletAddress="0xe692...47C3"
        network="Mainnet"
        theme="dark"
        onConnect={() => console.log('Connect wallet')}
        onThemeToggle={() => console.log('Toggle theme')}
      >
        <PortfolioComponent
          summary={data.summary as any}
          activeVaults={data.activeVaults as any}
          settledVaults={data.settledVaults as any}
          onVaultClick={(pool) =>
            console.log('Navigate to vault:', pool.join('/'))
          }
        />
      </AppShell>
    </>
  )
}
