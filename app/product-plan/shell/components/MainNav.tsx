import React from 'react'
import {
  BarChart3,
  Wallet,
  BookOpen,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react'

export interface NavItem {
  id: string
  label: string
  href: string
  icon: 'pools' | 'portfolio' | 'research' | 'settings'
}

export interface MainNavProps {
  items: NavItem[]
  activeItem: string
  onItemClick: (href: string) => void
  collapsed: boolean
  onToggleCollapse: () => void
}

const iconMap: Record<NavItem['icon'], React.ElementType> = {
  pools: BarChart3,
  portfolio: Wallet,
  research: BookOpen,
  settings: Settings,
}

export function MainNav({
  items,
  activeItem,
  onItemClick,
  collapsed,
  onToggleCollapse,
}: MainNavProps) {
  const mainItems = items.filter((item) => item.icon !== 'settings')
  const settingsItem = items.find((item) => item.icon === 'settings')

  return (
    <div className="flex h-full flex-col font-[family-name:'IBM_Plex_Sans']">
      {/* Logo */}
      <div className="flex h-12 items-center border-b border-zinc-800 px-4">
        {collapsed ? (
          <span className="text-lg font-semibold italic text-slate-200 font-[family-name:'Instrument_Serif']">
            T
          </span>
        ) : (
          <span className="text-lg font-semibold italic text-slate-200 font-[family-name:'Instrument_Serif']">
            ThetaSwap
          </span>
        )}
      </div>

      {/* Main Nav Items */}
      <nav className="flex-1 px-2 py-3">
        <ul className="flex flex-col gap-1">
          {mainItems.map((item) => {
            const Icon = iconMap[item.icon]
            const isActive = activeItem.startsWith(item.href)

            return (
              <li key={item.id}>
                <button
                  onClick={() => onItemClick(item.href)}
                  className={`group relative flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors duration-200 ${
                    isActive
                      ? 'bg-amber-500/10 text-amber-500'
                      : 'text-slate-400 hover:bg-zinc-800 hover:text-slate-200'
                  }`}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-amber-500" />
                  )}

                  <Icon className="h-4.5 w-4.5 flex-shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </button>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Separator + Bottom Section */}
      <div className="border-t border-zinc-800 px-2 py-3">
        {/* Settings */}
        {settingsItem && (
          <button
            onClick={() => onItemClick(settingsItem.href)}
            className={`group flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors duration-200 ${
              activeItem === settingsItem.href
                ? 'bg-amber-500/10 text-amber-500'
                : 'text-slate-400 hover:bg-zinc-800 hover:text-slate-200'
            }`}
          >
            <Settings className="h-4.5 w-4.5 flex-shrink-0" />
            {!collapsed && <span>{settingsItem.label}</span>}
          </button>
        )}

        {/* Collapse Toggle */}
        <button
          onClick={onToggleCollapse}
          className="mt-1 flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-slate-500 transition-colors duration-200 hover:bg-zinc-800 hover:text-slate-300"
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4.5 w-4.5 flex-shrink-0" />
          ) : (
            <>
              <PanelLeftClose className="h-4.5 w-4.5 flex-shrink-0" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
