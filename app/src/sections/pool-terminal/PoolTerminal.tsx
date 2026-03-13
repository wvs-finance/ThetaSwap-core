import { useState } from 'react'
import { PoolTerminal as PoolTerminalComponent } from './components/PoolTerminal'
import data from '@/../product/sections/pool-terminal/data.json'
import { AppShell } from '../../shell/components'
import type { NavItem } from '../../shell/components/MainNav'

const navigationItems: NavItem[] = [
  { id: 'pools', label: 'Pools', href: '/pools', icon: 'pools' },
  { id: 'portfolio', label: 'Portfolio', href: '/portfolio', icon: 'portfolio' },
  { id: 'research', label: 'Research', href: '/research', icon: 'research' },
]

export default function PoolTerminalPreview() {
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
        breadcrumbs={[
          { label: 'Pools', href: '/pools' },
          { label: `${data.pool.pair[0]}/${data.pool.pair[1]}` },
          { label: 'Terminal' },
        ]}
        sidebarCollapsed={sidebarCollapsed}
        onToggleSidebar={() => setSidebarCollapsed((c) => !c)}
        navigationItems={navigationItems}
        walletAddress="0xe692...47C3"
        network="Mainnet"
        theme="dark"
        onConnect={() => console.log('Connect wallet')}
        onThemeToggle={() => console.log('Toggle theme')}
      >
        <PoolTerminalComponent
          pool={data.pool as any}
          oracle={data.oracle as any}
          vault={data.vault as any}
          positions={data.positions as any}
          payoffCurve={data.payoffCurve as any}
          timeSeries={data.timeSeries as any}
          onDeposit={(amt) => console.log('Deposit:', amt)}
          onRedeemPair={(amt) => console.log('Redeem pair:', amt)}
          onPoke={() => console.log('Poke')}
          onRedeemLong={(amt) => console.log('Redeem LONG:', amt)}
          onRedeemShort={(amt) => console.log('Redeem SHORT:', amt)}
          onPositionClick={(pos) => console.log('Position:', pos.address)}
        />
      </AppShell>
    </>
  )
}
