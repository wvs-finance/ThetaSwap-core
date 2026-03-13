import { useState, useMemo } from 'react'
import { ChevronUp, ChevronDown, Info } from 'lucide-react'
import type { Pool, PoolExplorerProps, PoolFilters } from '../types'

// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

function formatTvl(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value}`
}

function formatBps(fee: number): string {
  return `${fee}bps`
}

function getSeverityColor(delta: number): string {
  if (delta > 0.8) return 'text-red-400'
  if (delta > 0.5) return 'text-orange-400'
  if (delta >= 0.2) return 'text-amber-400'
  return 'text-slate-400'
}

function getSeverityStroke(delta: number): string {
  if (delta > 0.8) return '#f87171'
  if (delta > 0.5) return '#fb923c'
  if (delta >= 0.2) return '#fbbf24'
  return '#94a3b8'
}

function daysUntil(timestamp: number): number {
  const now = Date.now() / 1000
  return Math.max(0, Math.ceil((timestamp - now) / 86400))
}

type SortColumn =
  | 'pair'
  | 'feeTier'
  | 'deltaPlusEpoch'
  | 'thetaSum'
  | 'positionCount'
  | 'tvl'
  | 'volume24h'
  | 'vault'

type SortDirection = 'asc' | 'desc'

// ---------------------------------------------------------------------------
// Sparkline
// ---------------------------------------------------------------------------

function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (!data.length) return null
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const w = 80
  const h = 24
  const pad = 1

  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w
    const y = pad + (1 - (v - min) / range) * (h - pad * 2)
    return `${x},${y}`
  })

  const polyline = points.join(' ')
  const areaPath = `M${points[0]} ${points.join(' L')} L${w},${h} L0,${h} Z`

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      width={w}
      height={h}
      className="inline-block align-middle"
    >
      <path d={areaPath} fill={color} fillOpacity={0.1} />
      <polyline
        points={polyline}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Vault badge
// ---------------------------------------------------------------------------

function VaultBadge({ vault }: { vault: Pool['vault'] }) {
  if (!vault) {
    return (
      <span className="inline-flex items-center rounded-sm bg-zinc-800 px-2 py-0.5 font-[family-name:'IBM_Plex_Mono'] text-xs text-zinc-500">
        &mdash;
      </span>
    )
  }

  if (vault.settled || vault.status === 'settled') {
    return (
      <span className="inline-flex items-center rounded-sm bg-slate-600/40 px-2 py-0.5 font-[family-name:'IBM_Plex_Mono'] text-xs text-slate-300">
        Settled
      </span>
    )
  }

  const days = daysUntil(vault.expiry)
  return (
    <span className="inline-flex items-center rounded-sm bg-amber-500/15 px-2 py-0.5 font-[family-name:'IBM_Plex_Mono'] text-xs text-amber-400">
      Active&nbsp;&middot;&nbsp;{days}d
    </span>
  )
}

// ---------------------------------------------------------------------------
// Column header
// ---------------------------------------------------------------------------

interface ColumnHeaderProps {
  label: string
  column: SortColumn
  sortColumn: SortColumn
  sortDirection: SortDirection
  onSort: (col: SortColumn) => void
  align?: 'left' | 'right'
  tooltip?: string
}

function ColumnHeader({
  label,
  column,
  sortColumn,
  sortDirection,
  onSort,
  align = 'left',
  tooltip,
}: ColumnHeaderProps) {
  const active = sortColumn === column
  return (
    <th
      className={`group cursor-pointer select-none whitespace-nowrap px-3 py-2.5 font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider ${
        active ? 'text-slate-300' : 'text-slate-500'
      } ${align === 'right' ? 'text-right' : 'text-left'}`}
      onClick={() => onSort(column)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {tooltip && (
          <span className="relative">
            <Info
              size={12}
              className="text-slate-600 transition-colors group-hover:text-slate-400"
            />
            <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2 rounded border border-zinc-700 bg-zinc-800 px-3 py-2 font-[family-name:'IBM_Plex_Sans'] text-[11px] font-normal normal-case tracking-normal text-slate-300 opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
              {tooltip}
            </span>
          </span>
        )}
        {active ? (
          sortDirection === 'asc' ? (
            <ChevronUp size={14} className="text-slate-400" />
          ) : (
            <ChevronDown size={14} className="text-slate-400" />
          )
        ) : (
          <ChevronUp size={14} className="text-transparent" />
        )}
      </span>
    </th>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function PoolExplorer({
  pools,
  onPoolClick,
  onSort,
  onFilter,
}: PoolExplorerProps) {
  const [sortColumn, setSortColumn] = useState<SortColumn>('deltaPlusEpoch')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [filters, setFilters] = useState<PoolFilters>({
    pair: '',
    vaultStatus: 'all',
  })

  // --- Sort handler ---
  function handleSort(col: SortColumn) {
    const newDir =
      col === sortColumn ? (sortDirection === 'asc' ? 'desc' : 'asc') : 'desc'
    setSortColumn(col)
    setSortDirection(newDir)
    onSort?.(col, newDir)
  }

  // --- Filter handler ---
  function updateFilter(patch: Partial<PoolFilters>) {
    const next = { ...filters, ...patch }
    setFilters(next)
    onFilter?.(next)
  }

  // --- Filtered + sorted pools ---
  const visiblePools = useMemo(() => {
    let list = [...pools]

    // Filter: pair search
    if (filters.pair) {
      const q = filters.pair.toUpperCase()
      list = list.filter(
        (p) =>
          p.pair[0].toUpperCase().includes(q) ||
          p.pair[1].toUpperCase().includes(q),
      )
    }

    // Filter: fee tier
    if (filters.feeTier) {
      list = list.filter((p) => p.feeTier === filters.feeTier)
    }

    // Filter: vault status
    if (filters.vaultStatus && filters.vaultStatus !== 'all') {
      list = list.filter((p) => {
        if (filters.vaultStatus === 'none') return p.vault === null
        if (filters.vaultStatus === 'active')
          return p.vault !== null && !p.vault.settled && p.vault.status === 'active'
        if (filters.vaultStatus === 'settled')
          return p.vault !== null && (p.vault.settled || p.vault.status === 'settled')
        return true
      })
    }

    // Sort
    list.sort((a, b) => {
      let cmp = 0
      switch (sortColumn) {
        case 'pair':
          cmp = `${a.pair[0]}/${a.pair[1]}`.localeCompare(
            `${b.pair[0]}/${b.pair[1]}`,
          )
          break
        case 'feeTier':
          cmp = a.feeTier - b.feeTier
          break
        case 'deltaPlusEpoch':
          cmp = a.deltaPlusEpoch - b.deltaPlusEpoch
          break
        case 'thetaSum':
          cmp = a.thetaSum - b.thetaSum
          break
        case 'positionCount':
          cmp = a.positionCount - b.positionCount
          break
        case 'tvl':
          cmp = a.tvl - b.tvl
          break
        case 'volume24h':
          cmp = a.volume24h - b.volume24h
          break
        case 'vault': {
          const rank = (p: Pool) =>
            p.vault === null ? 0 : p.vault.settled ? 1 : 2
          cmp = rank(a) - rank(b)
          break
        }
      }
      return sortDirection === 'asc' ? cmp : -cmp
    })

    return list
  }, [pools, filters, sortColumn, sortDirection])

  // --- Unique fee tiers for dropdown ---
  const feeTiers = useMemo(
    () => [...new Set(pools.map((p) => p.feeTier))].sort((a, b) => a - b),
    [pools],
  )

  return (
    <div className="flex h-full flex-col bg-zinc-950 text-slate-200">
      {/* ---- Filter bar ---- */}
      <div className="flex flex-shrink-0 items-center gap-3 border-b border-zinc-800 px-4 py-2.5">
        <input
          type="text"
          placeholder="Search pair..."
          value={filters.pair ?? ''}
          onChange={(e) => updateFilter({ pair: e.target.value })}
          className="h-8 w-44 rounded-none border border-zinc-700 bg-zinc-800 px-2.5 font-[family-name:'IBM_Plex_Sans'] text-xs text-slate-300 placeholder-zinc-500 outline-none transition-colors focus:border-slate-500"
        />

        <select
          value={filters.feeTier ?? ''}
          onChange={(e) =>
            updateFilter({
              feeTier: e.target.value ? Number(e.target.value) : undefined,
            })
          }
          className="h-8 rounded-none border border-zinc-700 bg-zinc-800 px-2 font-[family-name:'IBM_Plex_Sans'] text-xs text-slate-300 outline-none transition-colors focus:border-slate-500"
        >
          <option value="">All fees</option>
          {feeTiers.map((ft) => (
            <option key={ft} value={ft}>
              {formatBps(ft)}
            </option>
          ))}
        </select>

        <select
          value={filters.vaultStatus ?? 'all'}
          onChange={(e) =>
            updateFilter({
              vaultStatus: e.target.value as PoolFilters['vaultStatus'],
            })
          }
          className="h-8 rounded-none border border-zinc-700 bg-zinc-800 px-2 font-[family-name:'IBM_Plex_Sans'] text-xs text-slate-300 outline-none transition-colors focus:border-slate-500"
        >
          <option value="all">All vaults</option>
          <option value="active">Active</option>
          <option value="settled">Settled</option>
          <option value="none">No Vault</option>
        </select>

        <span className="ml-auto font-[family-name:'IBM_Plex_Mono'] text-xs text-zinc-500">
          {visiblePools.length} pool{visiblePools.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* ---- Table ---- */}
      <div className="flex-1 overflow-auto">
        <table className="w-full min-w-[1060px] border-collapse">
          <thead className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-900/95 backdrop-blur-sm">
            <tr>
              <ColumnHeader
                label="Pool"
                column="pair"
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
              <ColumnHeader
                label="Fee"
                column="feeTier"
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <ColumnHeader
                label="Delta-plus Epoch"
                column="deltaPlusEpoch"
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                onSort={handleSort}
                align="right"
                tooltip="Delta-plus = fee concentration severity. 0 = competitive, 1 = fully extracted. Derived from sum(1/block_lifetime_k) over position removals."
              />
              {/* Sparkline -- non-sortable */}
              <th className="px-3 py-2.5 font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                Trend
              </th>
              <ColumnHeader
                label="theta-sum"
                column="thetaSum"
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <ColumnHeader
                label="Positions"
                column="positionCount"
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <ColumnHeader
                label="TVL"
                column="tvl"
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <ColumnHeader
                label="24h Vol"
                column="volume24h"
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <ColumnHeader
                label="Vault"
                column="vault"
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
            </tr>
          </thead>
          <tbody>
            {visiblePools.map((pool, idx) => (
              <tr
                key={pool.poolKey}
                onClick={() => onPoolClick?.(pool)}
                className={`cursor-pointer border-b border-zinc-800/50 transition-colors hover:bg-zinc-800/60 ${
                  idx % 2 === 0 ? 'bg-zinc-900/50' : 'bg-zinc-950'
                }`}
              >
                {/* Pool pair */}
                <td className="whitespace-nowrap px-3 py-2 font-[family-name:'IBM_Plex_Sans'] text-sm font-medium text-slate-200">
                  {pool.pair[0]}
                  <span className="text-zinc-500"> / </span>
                  {pool.pair[1]}
                </td>

                {/* Fee tier */}
                <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs text-slate-400">
                  {formatBps(pool.feeTier)}
                </td>

                {/* Delta-plus epoch */}
                <td
                  className={`whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-sm tabular-nums ${getSeverityColor(pool.deltaPlusEpoch)}`}
                >
                  {pool.deltaPlusEpoch.toFixed(2)}
                </td>

                {/* Sparkline */}
                <td className="px-3 py-2">
                  <Sparkline
                    data={pool.sparkline}
                    color={getSeverityStroke(pool.deltaPlusEpoch)}
                  />
                </td>

                {/* theta-sum */}
                <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-400">
                  {pool.thetaSum.toFixed(2)}
                </td>

                {/* Positions */}
                <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-400">
                  {pool.positionCount.toLocaleString()}
                </td>

                {/* TVL */}
                <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-300">
                  {formatTvl(pool.tvl)}
                </td>

                {/* 24h Volume */}
                <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-400">
                  {formatTvl(pool.volume24h)}
                </td>

                {/* Vault */}
                <td className="whitespace-nowrap px-3 py-2">
                  <VaultBadge vault={pool.vault} />
                </td>
              </tr>
            ))}

            {visiblePools.length === 0 && (
              <tr>
                <td
                  colSpan={9}
                  className="px-3 py-12 text-center font-[family-name:'IBM_Plex_Sans'] text-sm text-zinc-500"
                >
                  No pools match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
