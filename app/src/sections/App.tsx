import { useState } from 'react'
import { AppShell } from '../shell/components'
import type { NavItem } from '../shell/components/MainNav'
import { PoolExplorer } from './pool-explorer/components/PoolExplorer'
import { PoolTerminal } from './pool-terminal/components/PoolTerminal'
import { Portfolio } from './portfolio/components/Portfolio'
import { Research } from './research/components/Research'

import poolExplorerData from '@/../product/sections/pool-explorer/data.json'
import poolTerminalData from '@/../product/sections/pool-terminal/data.json'
import portfolioData from '@/../product/sections/portfolio/data.json'
import researchData from '@/../product/sections/research/data.json'

const navigationItems: NavItem[] = [
  { id: 'pools', label: 'Pools', href: '/pools', icon: 'pools' },
  { id: 'portfolio', label: 'Portfolio', href: '/portfolio', icon: 'portfolio' },
  { id: 'research', label: 'Research', href: '/research', icon: 'research' },
]

type Route =
  | { page: 'pools' }
  | { page: 'terminal'; pool: [string, string] }
  | { page: 'portfolio' }
  | { page: 'research' }

export default function ThetaSwapApp() {
  const [route, setRoute] = useState<Route>({ page: 'pools' })
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  function navigate(href: string) {
    if (href === '/pools') setRoute({ page: 'pools' })
    else if (href === '/portfolio') setRoute({ page: 'portfolio' })
    else if (href === '/research') setRoute({ page: 'research' })
  }

  function currentPath() {
    switch (route.page) {
      case 'pools':
      case 'terminal':
        return '/pools'
      case 'portfolio':
        return '/portfolio'
      case 'research':
        return '/research'
    }
  }

  function breadcrumbs() {
    switch (route.page) {
      case 'pools':
        return [{ label: 'Pools' }]
      case 'terminal':
        return [
          { label: 'Pools', href: '/pools' },
          { label: `${route.pool[0]}/${route.pool[1]}` },
          { label: 'Terminal' },
        ]
      case 'portfolio':
        return [{ label: 'Portfolio' }]
      case 'research':
        return [{ label: 'Research' }]
    }
  }

  function renderContent() {
    switch (route.page) {
      case 'pools':
        return (
          <PoolExplorer
            pools={poolExplorerData.pools as any}
            onPoolClick={(pool) =>
              setRoute({ page: 'terminal', pool: pool.pair as [string, string] })
            }
            onSort={(col, dir) => console.log('Sort:', col, dir)}
            onFilter={(filters) => console.log('Filter:', filters)}
          />
        )
      case 'terminal':
        return (
          <PoolTerminal
            pool={poolTerminalData.pool as any}
            oracle={poolTerminalData.oracle as any}
            vault={poolTerminalData.vault as any}
            positions={poolTerminalData.positions as any}
            payoffCurve={poolTerminalData.payoffCurve as any}
            timeSeries={poolTerminalData.timeSeries as any}
            onDeposit={(amt) => console.log('Deposit:', amt)}
            onRedeemPair={(amt) => console.log('Redeem pair:', amt)}
            onPoke={() => console.log('Poke')}
            onRedeemLong={(amt) => console.log('Redeem LONG:', amt)}
            onRedeemShort={(amt) => console.log('Redeem SHORT:', amt)}
            onPositionClick={(pos) => console.log('Position:', pos.address)}
          />
        )
      case 'portfolio':
        return (
          <Portfolio
            summary={portfolioData.summary as any}
            activeVaults={portfolioData.activeVaults as any}
            settledVaults={portfolioData.settledVaults as any}
            onVaultClick={(pool) =>
              setRoute({ page: 'terminal', pool })
            }
          />
        )
      case 'research':
        return (
          <Research
            title={researchData.title}
            abstract={researchData.abstract}
            methodology={researchData.methodology as any}
            results={researchData.results as any}
            parameters={researchData.parameters as any}
            conclusion={researchData.conclusion}
          />
        )
    }
  }

  return (
    <>
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Instrument+Serif&display=swap"
      />
      <AppShell
        currentPath={currentPath()}
        onNavigate={navigate}
        breadcrumbs={breadcrumbs()}
        sidebarCollapsed={sidebarCollapsed}
        onToggleSidebar={() => setSidebarCollapsed((c) => !c)}
        navigationItems={navigationItems}
        walletAddress="0xe692...47C3"
        network="Mainnet"
        theme="dark"
        onConnect={() => console.log('Connect wallet')}
        onThemeToggle={() => console.log('Toggle theme')}
      >
        {renderContent()}
      </AppShell>
    </>
  )
}
