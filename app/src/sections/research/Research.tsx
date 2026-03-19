import { useState } from 'react'
import { Research as ResearchComponent } from './components/Research'
import data from '@/../product/sections/research/data.json'
import { AppShell } from '../../shell/components'
import type { NavItem } from '../../shell/components/MainNav'

const navigationItems: NavItem[] = [
  { id: 'pools', label: 'Pools', href: '/pools', icon: 'pools' },
  { id: 'portfolio', label: 'Portfolio', href: '/portfolio', icon: 'portfolio' },
  { id: 'research', label: 'Research', href: '/research', icon: 'research' },
]

export default function ResearchPreview() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <>
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Instrument+Serif&display=swap"
      />
      <AppShell
        currentPath="/research"
        onNavigate={(href) => console.log('Navigate:', href)}
        breadcrumbs={[{ label: 'Research' }]}
        sidebarCollapsed={sidebarCollapsed}
        onToggleSidebar={() => setSidebarCollapsed((c) => !c)}
        navigationItems={navigationItems}
        walletAddress="0xe692...47C3"
        network="Mainnet"
        theme="dark"
        onConnect={() => console.log('Connect wallet')}
        onThemeToggle={() => console.log('Toggle theme')}
      >
        <ResearchComponent
          title={data.title}
          abstract={data.abstract}
          methodology={data.methodology as any}
          results={data.results as any}
          parameters={data.parameters as any}
          conclusion={data.conclusion}
        />
      </AppShell>
    </>
  )
}
