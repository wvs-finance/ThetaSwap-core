import React from 'react'
import { Sun, Moon } from 'lucide-react'

export interface UserMenuProps {
  walletAddress?: string
  network?: string
  theme?: 'dark' | 'light'
  onConnect?: () => void
  onThemeToggle?: () => void
}

function truncateAddress(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

export function UserMenu({
  walletAddress,
  network = 'Mainnet',
  theme = 'dark',
  onConnect,
  onThemeToggle,
}: UserMenuProps) {
  return (
    <div className="flex items-center gap-3 font-[family-name:'IBM_Plex_Sans']">
      {/* Network Indicator */}
      <span className="flex items-center gap-1.5 rounded-md bg-zinc-800 px-2.5 py-1 text-xs text-slate-400">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        {network}
      </span>

      {/* Wallet Button */}
      {walletAddress ? (
        <button className="rounded-md border border-zinc-700 px-3 py-1 text-xs text-slate-300 transition-colors duration-200 hover:border-amber-500 hover:text-amber-500">
          {truncateAddress(walletAddress)}
        </button>
      ) : (
        <button
          onClick={onConnect}
          className="rounded-md border border-slate-400 px-3 py-1 text-xs text-slate-300 transition-colors duration-200 hover:border-amber-500 hover:text-amber-500"
        >
          Connect Wallet
        </button>
      )}

      {/* Theme Toggle */}
      <button
        onClick={onThemeToggle}
        className="rounded-md p-1.5 text-slate-400 transition-colors duration-200 hover:bg-zinc-800 hover:text-slate-200"
      >
        {theme === 'dark' ? (
          <Sun className="h-4 w-4" />
        ) : (
          <Moon className="h-4 w-4" />
        )}
      </button>
    </div>
  )
}
