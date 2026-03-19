import type {
  PortfolioProps,
  ActiveVault,
  SettledVault,
} from '../types'

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function formatUsd(value: number): string {
  const abs = Math.abs(value)
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(1)}K`
  return `$${value.toLocaleString()}`
}

function formatBalance(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return value.toLocaleString()
}

function daysUntil(timestamp: number): string {
  const now = Date.now() / 1000
  const diff = timestamp - now
  if (diff <= 0) return 'Expired'
  const d = Math.ceil(diff / 86400)
  return `${d}d`
}

function formatDate(timestamp: number): string {
  const d = new Date(timestamp * 1000)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// ---------------------------------------------------------------------------
// Stat Card
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  color,
}: {
  label: string
  value: string
  color?: string
}) {
  return (
    <div className="flex flex-1 flex-col gap-1 rounded-none border border-zinc-800 bg-zinc-900 p-4">
      <span className="font-[family-name:'Instrument_Serif'] text-xs italic text-zinc-500">
        {label}
      </span>
      <span
        className={`font-[family-name:'IBM_Plex_Mono'] text-xl tabular-nums ${color ?? 'text-slate-200'}`}
      >
        {value}
      </span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function Portfolio({
  summary,
  activeVaults,
  settledVaults,
  onVaultClick,
}: PortfolioProps) {
  const pnlColor =
    summary.netPnl > 0
      ? 'text-emerald-400'
      : summary.netPnl < 0
        ? 'text-red-400'
        : 'text-slate-200'

  const pnlPrefix = summary.netPnl > 0 ? '+' : ''

  return (
    <div className="flex h-full flex-col bg-zinc-950 text-slate-200 font-[family-name:'IBM_Plex_Sans']">
      {/* ---- Summary Strip ---- */}
      <div className="flex gap-3 border-b border-zinc-800 p-4">
        <StatCard label="Total Deposited" value={formatUsd(summary.totalDeposited)} />
        <StatCard label="LONG Value" value={formatUsd(summary.longValue)} />
        <StatCard label="SHORT Value" value={formatUsd(summary.shortValue)} />
        <StatCard
          label="Net P&L"
          value={`${pnlPrefix}${formatUsd(summary.netPnl)}`}
          color={pnlColor}
        />
      </div>

      {/* ---- Tables ---- */}
      <div className="flex-1 overflow-auto">
        {/* Active Vaults */}
        <div className="p-4">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="font-[family-name:'Instrument_Serif'] text-sm italic text-slate-300">
              Active Vaults
            </h2>
            <span className="font-[family-name:'IBM_Plex_Mono'] text-[10px] text-zinc-500">
              {activeVaults.length} vault{activeVaults.length !== 1 ? 's' : ''}
            </span>
          </div>
          <table className="w-full border-collapse">
            <thead className="border-b border-zinc-800 bg-zinc-900/95">
              <tr>
                <th className="whitespace-nowrap px-3 py-2.5 text-left font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                  Pool
                </th>
                <th className="whitespace-nowrap px-3 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                  LONG
                </th>
                <th className="whitespace-nowrap px-3 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                  SHORT
                </th>
                <th className="whitespace-nowrap px-3 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                  Strike
                </th>
                <th className="whitespace-nowrap px-3 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                  Expiry
                </th>
                <th className="whitespace-nowrap px-3 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                  Payout Preview
                </th>
                <th className="whitespace-nowrap px-3 py-2.5 font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {activeVaults.map((v, idx) => (
                <ActiveVaultRow
                  key={`${v.pool[0]}-${v.pool[1]}`}
                  vault={v}
                  idx={idx}
                  onClick={() => onVaultClick?.(v.pool)}
                />
              ))}
            </tbody>
          </table>
        </div>

        {/* Settled Vaults */}
        {settledVaults.length > 0 && (
          <div className="p-4 pt-0">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="font-[family-name:'Instrument_Serif'] text-sm italic text-slate-300">
                Settled Vaults
              </h2>
              <span className="font-[family-name:'IBM_Plex_Mono'] text-[10px] text-zinc-500">
                {settledVaults.length} settled
              </span>
            </div>
            <table className="w-full border-collapse">
              <thead className="border-b border-zinc-800 bg-zinc-900/95">
                <tr>
                  <th className="whitespace-nowrap px-3 py-2.5 text-left font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                    Pool
                  </th>
                  <th className="whitespace-nowrap px-3 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                    Settlement
                  </th>
                  <th className="whitespace-nowrap px-3 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                    LONG Payout
                  </th>
                  <th className="whitespace-nowrap px-3 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                    SHORT Payout
                  </th>
                  <th className="whitespace-nowrap px-3 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
                    Net Result
                  </th>
                </tr>
              </thead>
              <tbody>
                {settledVaults.map((v, idx) => (
                  <SettledVaultRow
                    key={`${v.pool[0]}-${v.pool[1]}`}
                    vault={v}
                    idx={idx}
                    onClick={() => onVaultClick?.(v.pool)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Table rows
// ---------------------------------------------------------------------------

function ActiveVaultRow({
  vault,
  idx,
  onClick,
}: {
  vault: ActiveVault
  idx: number
  onClick: () => void
}) {
  return (
    <tr
      onClick={onClick}
      className={`cursor-pointer border-b border-zinc-800/50 transition-colors hover:bg-zinc-800/60 ${
        idx % 2 === 0 ? 'bg-zinc-900/50' : 'bg-zinc-950'
      }`}
    >
      <td className="whitespace-nowrap px-3 py-2 font-[family-name:'IBM_Plex_Sans'] text-sm font-medium text-slate-200">
        {vault.pool[0]}
        <span className="text-zinc-500"> / </span>
        {vault.pool[1]}
        <span className="ml-1.5 font-[family-name:'IBM_Plex_Mono'] text-[10px] text-zinc-500">
          {vault.feeTier}bps
        </span>
      </td>
      <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-300">
        {formatBalance(vault.longBalance)}
      </td>
      <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-300">
        {formatBalance(vault.shortBalance)}
      </td>
      <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-400">
        {vault.strike.toFixed(2)}
      </td>
      <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-400">
        {daysUntil(vault.expiry)}
      </td>
      <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-[11px] tabular-nums">
        <span className="text-amber-400">{(vault.payoutPreview.long * 100).toFixed(1)}%</span>
        <span className="text-zinc-600"> / </span>
        <span className="text-slate-400">{(vault.payoutPreview.short * 100).toFixed(1)}%</span>
      </td>
      <td className="whitespace-nowrap px-3 py-2">
        <span className="inline-flex items-center rounded-sm bg-amber-500/15 px-2 py-0.5 font-[family-name:'IBM_Plex_Mono'] text-[10px] text-amber-400">
          Active
        </span>
      </td>
    </tr>
  )
}

function SettledVaultRow({
  vault,
  idx,
  onClick,
}: {
  vault: SettledVault
  idx: number
  onClick: () => void
}) {
  const resultColor = vault.netResult > 0 ? 'text-emerald-400' : 'text-red-400'
  const resultPrefix = vault.netResult > 0 ? '+' : ''

  return (
    <tr
      onClick={onClick}
      className={`cursor-pointer border-b border-zinc-800/50 transition-colors hover:bg-zinc-800/60 ${
        idx % 2 === 0 ? 'bg-zinc-900/50' : 'bg-zinc-950'
      }`}
    >
      <td className="whitespace-nowrap px-3 py-2 font-[family-name:'IBM_Plex_Sans'] text-sm font-medium text-slate-200">
        {vault.pool[0]}
        <span className="text-zinc-500"> / </span>
        {vault.pool[1]}
      </td>
      <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-400">
        {formatDate(vault.settlementDate)}
      </td>
      <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-300">
        {formatUsd(vault.longPayout)}
      </td>
      <td className="whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums text-slate-300">
        {formatUsd(vault.shortPayout)}
      </td>
      <td className={`whitespace-nowrap px-3 py-2 text-right font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums ${resultColor}`}>
        {resultPrefix}{formatUsd(vault.netResult)}
      </td>
    </tr>
  )
}
