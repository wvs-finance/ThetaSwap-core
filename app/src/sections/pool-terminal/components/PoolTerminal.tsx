import { useState, useMemo } from 'react'
import { ChevronUp, ChevronDown, Info, ChevronRight } from 'lucide-react'
import type {
  PoolTerminalProps,
  Position,
  PayoffPoint,
  TimeSeriesPoint,
} from '@/../product/sections/pool-terminal/types'

// ---------------------------------------------------------------------------
// Shared utilities
// ---------------------------------------------------------------------------

function getSeverityColor(delta: number): string {
  if (delta > 0.8) return 'text-red-400'
  if (delta > 0.5) return 'text-orange-400'
  if (delta >= 0.2) return 'text-amber-400'
  return 'text-slate-400'
}

function getSeverityHex(delta: number): string {
  if (delta > 0.8) return '#f87171'
  if (delta > 0.5) return '#fb923c'
  if (delta >= 0.2) return '#fbbf24'
  return '#94a3b8'
}

function formatLiquidity(liq: number): string {
  if (liq >= 1e15) return `${(liq / 1e15).toFixed(1)}P`
  if (liq >= 1e12) return `${(liq / 1e12).toFixed(1)}T`
  if (liq >= 1e9) return `${(liq / 1e9).toFixed(1)}B`
  if (liq >= 1e6) return `${(liq / 1e6).toFixed(1)}M`
  return liq.toLocaleString()
}

function formatUsd(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value.toFixed(0)}`
}

function formatTick(tick: number): string {
  if (tick === -887220 || tick === 887220) return tick === -887220 ? 'MIN' : 'MAX'
  return tick.toLocaleString()
}

function timeAgo(timestamp: number): string {
  const now = Date.now() / 1000
  const diff = now - timestamp
  if (diff < 60) return `${Math.floor(diff)}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function daysUntil(timestamp: number): string {
  const now = Date.now() / 1000
  const diff = timestamp - now
  if (diff <= 0) return 'Expired'
  const d = Math.ceil(diff / 86400)
  return `${d}d`
}

// ---------------------------------------------------------------------------
// Position table sort
// ---------------------------------------------------------------------------

type PosSortCol = 'address' | 'tickRange' | 'liquidity' | 'feeRevenue' | 'blockLifetime' | 'maxDelta'
type SortDir = 'asc' | 'desc'

// ---------------------------------------------------------------------------
// Payoff Curve (SVG)
// ---------------------------------------------------------------------------

function PayoffCurve({
  data,
  currentDelta,
  strike,
  hwm,
}: {
  data: PayoffPoint[]
  currentDelta: number
  strike: number
  hwm: number
}) {
  const W = 280
  const H = 160
  const pad = { top: 12, right: 16, bottom: 28, left: 36 }
  const cw = W - pad.left - pad.right
  const ch = H - pad.top - pad.bottom

  const x = (d: number) => pad.left + d * cw
  const y = (p: number) => pad.top + (1 - p) * ch

  // Build path
  const pathD = data
    .map((pt, i) => `${i === 0 ? 'M' : 'L'}${x(pt.deltaPlus).toFixed(1)},${y(pt.longPayout).toFixed(1)}`)
    .join(' ')

  // Area fill
  const areaD = `${pathD} L${x(data[data.length - 1].deltaPlus).toFixed(1)},${y(0).toFixed(1)} L${x(data[0].deltaPlus).toFixed(1)},${y(0).toFixed(1)} Z`

  // Current delta position on curve
  const curPayout = data.reduce((best, pt) =>
    Math.abs(pt.deltaPlus - currentDelta) < Math.abs(best.deltaPlus - currentDelta) ? pt : best
  ).longPayout

  // HWM payout
  const hwmPayout = data.reduce((best, pt) =>
    Math.abs(pt.deltaPlus - hwm) < Math.abs(best.deltaPlus - hwm) ? pt : best
  ).longPayout

  // Y-axis ticks
  const yTicks = [0, 0.25, 0.5, 0.75, 1.0]
  // X-axis ticks
  const xTicks = [0, 0.25, 0.5, 0.75, 1.0]

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 180 }}>
      {/* Grid lines */}
      {yTicks.map((t) => (
        <line
          key={`yg-${t}`}
          x1={pad.left}
          y1={y(t)}
          x2={W - pad.right}
          y2={y(t)}
          stroke="#3f3f46"
          strokeWidth={0.5}
        />
      ))}

      {/* Strike line */}
      <line
        x1={x(strike)}
        y1={pad.top}
        x2={x(strike)}
        y2={H - pad.bottom}
        stroke="#94a3b8"
        strokeWidth={1}
        strokeDasharray="4,3"
      />
      <text
        x={x(strike)}
        y={pad.top - 3}
        textAnchor="middle"
        className="fill-slate-500"
        fontSize={8}
        fontFamily="'IBM Plex Mono', monospace"
      >
        K={strike}
      </text>

      {/* Payoff area fill */}
      <path d={areaD} fill="#fbbf24" fillOpacity={0.06} />

      {/* Payoff curve line */}
      <path d={pathD} fill="none" stroke="#fbbf24" strokeWidth={1.5} strokeLinejoin="round" />

      {/* Current Δ⁺ marker */}
      <line
        x1={x(currentDelta)}
        y1={pad.top}
        x2={x(currentDelta)}
        y2={H - pad.bottom}
        stroke={getSeverityHex(currentDelta)}
        strokeWidth={1}
        strokeDasharray="2,2"
      />
      <circle
        cx={x(currentDelta)}
        cy={y(curPayout)}
        r={4}
        fill={getSeverityHex(currentDelta)}
        stroke="#18181b"
        strokeWidth={1.5}
      />

      {/* HWM dot */}
      <circle
        cx={x(hwm)}
        cy={y(hwmPayout)}
        r={3.5}
        fill="none"
        stroke="#e2e8f0"
        strokeWidth={1.5}
      />
      <text
        x={x(hwm) + 6}
        y={y(hwmPayout) - 4}
        className="fill-slate-400"
        fontSize={7}
        fontFamily="'IBM Plex Mono', monospace"
      >
        HWM
      </text>

      {/* Y-axis labels */}
      {yTicks.map((t) => (
        <text
          key={`yl-${t}`}
          x={pad.left - 4}
          y={y(t) + 3}
          textAnchor="end"
          className="fill-zinc-500"
          fontSize={8}
          fontFamily="'IBM Plex Mono', monospace"
        >
          {t.toFixed(2)}
        </text>
      ))}

      {/* X-axis labels */}
      {xTicks.map((t) => (
        <text
          key={`xl-${t}`}
          x={x(t)}
          y={H - pad.bottom + 12}
          textAnchor="middle"
          className="fill-zinc-500"
          fontSize={8}
          fontFamily="'IBM Plex Mono', monospace"
        >
          {t.toFixed(2)}
        </text>
      ))}

      {/* Axis labels */}
      <text
        x={W / 2}
        y={H - 2}
        textAnchor="middle"
        className="fill-zinc-600"
        fontSize={8}
        fontFamily="'IBM Plex Sans', sans-serif"
      >
        Δ⁺
      </text>
      <text
        x={6}
        y={H / 2}
        textAnchor="middle"
        className="fill-zinc-600"
        fontSize={8}
        fontFamily="'IBM Plex Sans', sans-serif"
        transform={`rotate(-90, 6, ${H / 2})`}
      >
        LONG Payout
      </text>
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Time Series Chart (SVG)
// ---------------------------------------------------------------------------

function TimeSeriesChart({
  data,
  range,
}: {
  data: TimeSeriesPoint[]
  range: string
}) {
  const filtered = useMemo(() => {
    if (range === 'All' || !data.length) return data
    const now = data[data.length - 1].timestamp
    const cutoff: Record<string, number> = {
      '1D': 86400,
      '7D': 86400 * 7,
      '30D': 86400 * 30,
    }
    const limit = cutoff[range] ?? Infinity
    return data.filter((pt) => now - pt.timestamp <= limit)
  }, [data, range])

  if (!filtered.length) return null

  const W = 900
  const H = 120
  const pad = { top: 8, right: 16, bottom: 20, left: 40 }
  const cw = W - pad.left - pad.right
  const ch = H - pad.top - pad.bottom

  const tMin = filtered[0].timestamp
  const tMax = filtered[filtered.length - 1].timestamp
  const tRange = tMax - tMin || 1

  const allVals = filtered.flatMap((pt) => [pt.deltaPlus, pt.hwm])
  const vMin = 0
  const vMax = Math.max(0.5, Math.ceil(Math.max(...allVals) * 10) / 10)
  const vRange = vMax - vMin || 1

  const tx = (t: number) => pad.left + ((t - tMin) / tRange) * cw
  const vy = (v: number) => pad.top + (1 - (v - vMin) / vRange) * ch

  // Δ⁺ line
  const deltaPath = filtered
    .map((pt, i) => `${i === 0 ? 'M' : 'L'}${tx(pt.timestamp).toFixed(1)},${vy(pt.deltaPlus).toFixed(1)}`)
    .join(' ')

  // HWM line
  const hwmPath = filtered
    .map((pt, i) => `${i === 0 ? 'M' : 'L'}${tx(pt.timestamp).toFixed(1)},${vy(pt.hwm).toFixed(1)}`)
    .join(' ')

  // Epoch boundaries
  const epochs = filtered.filter((pt) => pt.epochBoundary)

  // Y-axis ticks
  const yTicks = Array.from({ length: 6 }, (_, i) => vMin + (i / 5) * vRange)

  // Date labels
  const dateLabels = useMemo(() => {
    const count = Math.min(6, filtered.length)
    const step = Math.floor(filtered.length / count)
    return filtered.filter((_, i) => i % step === 0 || i === filtered.length - 1)
  }, [filtered])

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" preserveAspectRatio="none" style={{ height: '100%' }}>
      {/* Grid */}
      {yTicks.map((t, i) => (
        <line
          key={`tsg-${i}`}
          x1={pad.left}
          y1={vy(t)}
          x2={W - pad.right}
          y2={vy(t)}
          stroke="#27272a"
          strokeWidth={0.5}
        />
      ))}

      {/* Epoch boundaries */}
      {epochs.map((ep, i) => (
        <line
          key={`eb-${i}`}
          x1={tx(ep.timestamp)}
          y1={pad.top}
          x2={tx(ep.timestamp)}
          y2={H - pad.bottom}
          stroke="#52525b"
          strokeWidth={1}
          strokeDasharray="4,4"
        />
      ))}

      {/* HWM area fill */}
      <path
        d={`${hwmPath} L${tx(filtered[filtered.length - 1].timestamp).toFixed(1)},${vy(0).toFixed(1)} L${tx(filtered[0].timestamp).toFixed(1)},${vy(0).toFixed(1)} Z`}
        fill="#94a3b8"
        fillOpacity={0.04}
      />

      {/* HWM line */}
      <path d={hwmPath} fill="none" stroke="#64748b" strokeWidth={1} strokeDasharray="3,2" />

      {/* Δ⁺ area fill */}
      <path
        d={`${deltaPath} L${tx(filtered[filtered.length - 1].timestamp).toFixed(1)},${vy(0).toFixed(1)} L${tx(filtered[0].timestamp).toFixed(1)},${vy(0).toFixed(1)} Z`}
        fill="#fbbf24"
        fillOpacity={0.06}
      />

      {/* Δ⁺ line */}
      <path d={deltaPath} fill="none" stroke="#fbbf24" strokeWidth={1.5} strokeLinejoin="round" />

      {/* Y-axis labels */}
      {yTicks.filter((_, i) => i % 2 === 0).map((t, i) => (
        <text
          key={`tyl-${i}`}
          x={pad.left - 4}
          y={vy(t) + 3}
          textAnchor="end"
          className="fill-zinc-500"
          fontSize={8}
          fontFamily="'IBM Plex Mono', monospace"
        >
          {t.toFixed(2)}
        </text>
      ))}

      {/* Date labels */}
      {dateLabels.map((pt, i) => {
        const d = new Date(pt.timestamp * 1000)
        const label = `${d.getMonth() + 1}/${d.getDate()}`
        return (
          <text
            key={`dl-${i}`}
            x={tx(pt.timestamp)}
            y={H - 4}
            textAnchor="middle"
            className="fill-zinc-600"
            fontSize={7}
            fontFamily="'IBM Plex Mono', monospace"
          >
            {label}
          </text>
        )
      })}

      {/* Legend */}
      <line x1={pad.left + 4} y1={6} x2={pad.left + 16} y2={6} stroke="#fbbf24" strokeWidth={1.5} />
      <text x={pad.left + 20} y={9} className="fill-zinc-400" fontSize={7} fontFamily="'IBM Plex Sans', sans-serif">
        Δ⁺
      </text>
      <line x1={pad.left + 40} y1={6} x2={pad.left + 52} y2={6} stroke="#64748b" strokeWidth={1} strokeDasharray="3,2" />
      <text x={pad.left + 56} y={9} className="fill-zinc-500" fontSize={7} fontFamily="'IBM Plex Sans', sans-serif">
        HWM
      </text>
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function PoolTerminal({
  pool,
  oracle,
  vault,
  positions,
  payoffCurve,
  timeSeries,
  onDeposit,
  onRedeemPair,
  onPoke,
  onRedeemLong,
  onRedeemShort,
  onPositionClick,
}: PoolTerminalProps) {
  // Position table state
  const [posSortCol, setPosSortCol] = useState<PosSortCol>('maxDelta')
  const [posSortDir, setPosSortDir] = useState<SortDir>('desc')
  const [expandedPos, setExpandedPos] = useState<string | null>(null)
  const [tsRange, setTsRange] = useState('30D')

  function handlePosSort(col: PosSortCol) {
    if (col === posSortCol) {
      setPosSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setPosSortCol(col)
      setPosSortDir('desc')
    }
  }

  const sortedPositions = useMemo(() => {
    const list = [...positions]
    list.sort((a, b) => {
      let cmp = 0
      switch (posSortCol) {
        case 'address':
          cmp = a.address.localeCompare(b.address)
          break
        case 'tickRange':
          cmp = (a.tickUpper - a.tickLower) - (b.tickUpper - b.tickLower)
          break
        case 'liquidity':
          cmp = a.liquidity - b.liquidity
          break
        case 'feeRevenue':
          cmp = a.feeRevenue1 - b.feeRevenue1
          break
        case 'blockLifetime':
          cmp = a.blockLifetime - b.blockLifetime
          break
        case 'maxDelta':
          cmp = a.maxDelta - b.maxDelta
          break
      }
      return posSortDir === 'asc' ? cmp : -cmp
    })
    return list
  }, [positions, posSortCol, posSortDir])

  // Column header helper for position table
  function PosColHeader({
    label,
    col,
    align = 'left',
    tooltip,
  }: {
    label: string
    col: PosSortCol
    align?: 'left' | 'right'
    tooltip?: string
  }) {
    const active = posSortCol === col
    return (
      <th
        className={`group cursor-pointer select-none whitespace-nowrap px-2 py-2 font-[family-name:'IBM_Plex_Sans'] text-[10px] font-medium uppercase tracking-wider ${
          active ? 'text-slate-300' : 'text-slate-500'
        } ${align === 'right' ? 'text-right' : 'text-left'}`}
        onClick={() => handlePosSort(col)}
      >
        <span className="inline-flex items-center gap-0.5">
          {label}
          {tooltip && (
            <span className="relative">
              <Info size={10} className="text-slate-600 transition-colors group-hover:text-slate-400" />
              <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-52 -translate-x-1/2 rounded border border-zinc-700 bg-zinc-800 px-2 py-1.5 font-[family-name:'IBM_Plex_Sans'] text-[10px] font-normal normal-case tracking-normal text-slate-300 opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                {tooltip}
              </span>
            </span>
          )}
          {active ? (
            posSortDir === 'asc' ? (
              <ChevronUp size={12} className="text-slate-400" />
            ) : (
              <ChevronDown size={12} className="text-slate-400" />
            )
          ) : (
            <ChevronUp size={12} className="text-transparent" />
          )}
        </span>
      </th>
    )
  }

  return (
    <div className="flex h-full flex-col bg-zinc-950 text-slate-200 font-[family-name:'IBM_Plex_Sans']">
      {/* ================================================================
          TOP SECTION: Left (positions) + Right (oracle/vault/payoff)
          ================================================================ */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* ---- LEFT PANE: Position Table (45%) ---- */}
        <div className="flex w-[45%] flex-col border-r border-zinc-800">
          <div className="flex items-center justify-between border-b border-zinc-800 px-3 py-2">
            <h2 className="font-[family-name:'Instrument_Serif'] text-sm italic text-slate-300">
              Positions
            </h2>
            <span className="font-[family-name:'IBM_Plex_Mono'] text-[10px] text-zinc-500">
              {positions.length} positions
            </span>
          </div>
          <div className="flex-1 overflow-auto">
            <table className="w-full min-w-[580px] border-collapse">
              <thead className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-900/95 backdrop-blur-sm">
                <tr>
                  <PosColHeader label="Address" col="address" />
                  <PosColHeader label="Tick Range" col="tickRange" />
                  <PosColHeader label="Liquidity" col="liquidity" align="right" />
                  <PosColHeader
                    label="Fees (USDC)"
                    col="feeRevenue"
                    align="right"
                    tooltip="Cumulative fee revenue in token1 (USDC)"
                  />
                  <PosColHeader
                    label="Blocks"
                    col="blockLifetime"
                    align="right"
                    tooltip="Block lifetime = blocks between position add and remove"
                  />
                  <PosColHeader
                    label="Max Δ⁺"
                    col="maxDelta"
                    align="right"
                    tooltip="Highest Δ⁺ epoch observed during this position's lifetime"
                  />
                </tr>
              </thead>
              <tbody>
                {sortedPositions.map((pos, idx) => {
                  const isExpanded = expandedPos === pos.address
                  return (
                    <PosRow
                      key={pos.address + idx}
                      pos={pos}
                      idx={idx}
                      isExpanded={isExpanded}
                      onToggle={() => {
                        setExpandedPos(isExpanded ? null : pos.address)
                        onPositionClick?.(pos)
                      }}
                    />
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* ---- RIGHT PANE: Oracle + Vault + Payoff (remaining) ---- */}
        <div className="flex flex-1 flex-col overflow-auto">
          {/* Oracle State */}
          <div className="border-b border-zinc-800 p-3">
            <h2 className="mb-2 font-[family-name:'Instrument_Serif'] text-sm italic text-slate-300">
              Oracle State
            </h2>
            <div className="flex items-start gap-4">
              {/* Primary: Δ⁺ Epoch */}
              <div className="flex flex-col">
                <span className="text-[10px] uppercase tracking-wider text-zinc-500">
                  Δ⁺ Epoch
                </span>
                <span
                  className={`font-[family-name:'IBM_Plex_Mono'] text-3xl tabular-nums ${getSeverityColor(oracle.deltaPlusEpoch)}`}
                >
                  {oracle.deltaPlusEpoch.toFixed(3)}
                </span>
              </div>

              {/* Secondary metrics grid */}
              <div className="grid flex-1 grid-cols-2 gap-x-4 gap-y-1.5">
                <MetricRow label="Δ⁺ Cumul." value={oracle.deltaPlusCumulative.toFixed(3)} color={getSeverityColor(oracle.deltaPlusCumulative)} />
                <MetricRow label="atNull" value={oracle.atNull.toFixed(3)} tooltip="Competitive threshold: Δ⁺ = max(0, A_T - atNull)" />
                <MetricRow label="θ-sum" value={oracle.thetaSum.toFixed(2)} tooltip="Σ(1/ℓ_k) cumulative over position removals" />
                <MetricRow label="Removed" value={oracle.removedPosCount.toString()} />
                <div className="col-span-2 flex items-center gap-2">
                  <span className="text-[10px] text-zinc-500">Epoch</span>
                  <div className="h-1.5 flex-1 rounded-full bg-zinc-800">
                    <div
                      className="h-full rounded-full bg-amber-500/60"
                      style={{ width: `${oracle.epochProgress * 100}%` }}
                    />
                  </div>
                  <span className="font-[family-name:'IBM_Plex_Mono'] text-[10px] text-zinc-500">
                    {(oracle.epochProgress * 100).toFixed(0)}%
                  </span>
                </div>
                <MetricRow label="Last Poke" value={timeAgo(oracle.lastPokeTimestamp)} />
              </div>
            </div>
          </div>

          {/* Vault State */}
          <div className="border-b border-zinc-800 p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="font-[family-name:'Instrument_Serif'] text-sm italic text-slate-300">
                Vault
              </h2>
              {vault.settled ? (
                <span className="rounded-sm bg-slate-600/40 px-2 py-0.5 font-[family-name:'IBM_Plex_Mono'] text-[10px] text-slate-300">
                  Settled
                </span>
              ) : (
                <span className="rounded-sm bg-amber-500/15 px-2 py-0.5 font-[family-name:'IBM_Plex_Mono'] text-[10px] text-amber-400">
                  Active · {daysUntil(vault.expiry)}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 mb-3">
              <MetricRow label="Strike" value={vault.strike.toFixed(3)} />
              <MetricRow label="HWM" value={vault.hwm.toFixed(3)} color="text-slate-200" />
              <MetricRow label="Expiry" value={daysUntil(vault.expiry)} />
              <MetricRow label="Deposits" value={formatUsd(vault.totalDeposits)} />
            </div>

            {/* Action buttons */}
            {!vault.settled ? (
              <div className="flex gap-2">
                <button
                  onClick={() => onDeposit?.(0)}
                  className="flex-1 rounded-none border border-amber-500/40 bg-amber-500/10 px-3 py-1.5 font-[family-name:'IBM_Plex_Sans'] text-xs font-medium text-amber-400 transition-colors hover:bg-amber-500/20"
                >
                  Deposit
                </button>
                <button
                  onClick={() => onRedeemPair?.(0)}
                  className="flex-1 rounded-none border border-zinc-700 bg-zinc-800 px-3 py-1.5 font-[family-name:'IBM_Plex_Sans'] text-xs text-slate-400 transition-colors hover:bg-zinc-700"
                >
                  Redeem Pair
                </button>
                <button
                  onClick={() => onPoke?.()}
                  className="rounded-none border border-zinc-700 bg-zinc-800 px-3 py-1.5 font-[family-name:'IBM_Plex_Sans'] text-xs text-slate-400 transition-colors hover:bg-zinc-700"
                >
                  Poke
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => onRedeemLong?.(0)}
                  className="flex-1 rounded-none border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 font-[family-name:'IBM_Plex_Sans'] text-xs font-medium text-emerald-400 transition-colors hover:bg-emerald-500/20"
                >
                  Redeem LONG
                </button>
                <button
                  onClick={() => onRedeemShort?.(0)}
                  className="flex-1 rounded-none border border-zinc-700 bg-zinc-800 px-3 py-1.5 font-[family-name:'IBM_Plex_Sans'] text-xs text-slate-400 transition-colors hover:bg-zinc-700"
                >
                  Redeem SHORT
                </button>
              </div>
            )}
          </div>

          {/* Payoff Curve */}
          <div className="flex-1 p-3">
            <h2 className="mb-1 font-[family-name:'Instrument_Serif'] text-sm italic text-slate-300">
              Payoff Curve
            </h2>
            <p className="mb-2 text-[10px] text-zinc-500">
              LONG payout vs Δ⁺ · power-squared: max(0, ((HWM − K)/(1 − K))²)
            </p>
            <PayoffCurve
              data={payoffCurve}
              currentDelta={oracle.deltaPlusEpoch}
              strike={vault.strike}
              hwm={vault.hwm}
            />
          </div>
        </div>
      </div>

      {/* ================================================================
          BOTTOM STRIP: Time Series (20%)
          ================================================================ */}
      <div className="h-[20%] min-h-[120px] border-t border-zinc-800">
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b border-zinc-800 px-3 py-1.5">
            <h2 className="font-[family-name:'Instrument_Serif'] text-xs italic text-slate-300">
              Δ⁺ Time Series
            </h2>
            <div className="flex gap-1">
              {['1D', '7D', '30D', 'All'].map((r) => (
                <button
                  key={r}
                  onClick={() => setTsRange(r)}
                  className={`rounded-none px-2 py-0.5 font-[family-name:'IBM_Plex_Mono'] text-[10px] transition-colors ${
                    tsRange === r
                      ? 'bg-zinc-700 text-slate-200'
                      : 'text-zinc-500 hover:text-zinc-300'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 px-3 py-1">
            <TimeSeriesChart data={timeSeries} range={tsRange} />
          </div>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MetricRow({
  label,
  value,
  color,
  tooltip,
}: {
  label: string
  value: string
  color?: string
  tooltip?: string
}) {
  return (
    <div className="group relative flex items-baseline justify-between">
      <span className="text-[10px] text-zinc-500">
        {label}
        {tooltip && (
          <>
            {' '}
            <Info size={9} className="inline text-zinc-600 transition-colors group-hover:text-zinc-400" />
            <span className="pointer-events-none absolute bottom-full left-0 z-50 mb-1 w-48 rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-[10px] text-slate-300 opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
              {tooltip}
            </span>
          </>
        )}
      </span>
      <span className={`font-[family-name:'IBM_Plex_Mono'] text-xs tabular-nums ${color ?? 'text-slate-300'}`}>
        {value}
      </span>
    </div>
  )
}

function PosRow({
  pos,
  idx,
  isExpanded,
  onToggle,
}: {
  pos: Position
  idx: number
  isExpanded: boolean
  onToggle: () => void
}) {
  return (
    <>
      <tr
        onClick={onToggle}
        className={`cursor-pointer border-b border-zinc-800/50 transition-colors hover:bg-zinc-800/60 ${
          idx % 2 === 0 ? 'bg-zinc-900/50' : 'bg-zinc-950'
        } ${pos.isUser ? 'border-l-2 border-l-amber-500' : ''}`}
      >
        <td className="whitespace-nowrap px-2 py-1.5 font-[family-name:'IBM_Plex_Mono'] text-[11px] text-slate-400">
          <span className="inline-flex items-center gap-1">
            <ChevronRight
              size={10}
              className={`transition-transform ${isExpanded ? 'rotate-90' : ''} text-zinc-500`}
            />
            {pos.address}
          </span>
        </td>
        <td className="whitespace-nowrap px-2 py-1.5 font-[family-name:'IBM_Plex_Mono'] text-[11px] text-slate-400">
          [{formatTick(pos.tickLower)}, {formatTick(pos.tickUpper)}]
        </td>
        <td className="whitespace-nowrap px-2 py-1.5 text-right font-[family-name:'IBM_Plex_Mono'] text-[11px] tabular-nums text-slate-400">
          {formatLiquidity(pos.liquidity)}
        </td>
        <td className="whitespace-nowrap px-2 py-1.5 text-right font-[family-name:'IBM_Plex_Mono'] text-[11px] tabular-nums text-slate-300">
          {pos.feeRevenue1.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </td>
        <td className="whitespace-nowrap px-2 py-1.5 text-right font-[family-name:'IBM_Plex_Mono'] text-[11px] tabular-nums text-slate-400">
          {pos.blockLifetime.toLocaleString()}
        </td>
        <td className={`whitespace-nowrap px-2 py-1.5 text-right font-[family-name:'IBM_Plex_Mono'] text-[11px] tabular-nums ${getSeverityColor(pos.maxDelta)}`}>
          {pos.maxDelta.toFixed(2)}
        </td>
      </tr>
      {isExpanded && (
        <tr className="bg-zinc-900/80">
          <td colSpan={6} className="px-6 py-2">
            <div className="grid grid-cols-3 gap-4 text-[10px]">
              <div>
                <span className="text-zinc-500">ETH Fees:</span>{' '}
                <span className="font-[family-name:'IBM_Plex_Mono'] text-slate-300">
                  {pos.feeRevenue0.toFixed(4)} ETH
                </span>
              </div>
              <div>
                <span className="text-zinc-500">USDC Fees:</span>{' '}
                <span className="font-[family-name:'IBM_Plex_Mono'] text-slate-300">
                  ${pos.feeRevenue1.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div>
                <span className="text-zinc-500">Raw Liquidity:</span>{' '}
                <span className="font-[family-name:'IBM_Plex_Mono'] text-slate-300">
                  {pos.liquidity.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-zinc-500">Tick Range:</span>{' '}
                <span className="font-[family-name:'IBM_Plex_Mono'] text-slate-300">
                  [{pos.tickLower.toLocaleString()}, {pos.tickUpper.toLocaleString()}]
                </span>
              </div>
              <div>
                <span className="text-zinc-500">Width:</span>{' '}
                <span className="font-[family-name:'IBM_Plex_Mono'] text-slate-300">
                  {(pos.tickUpper - pos.tickLower).toLocaleString()} ticks
                </span>
              </div>
              <div>
                <span className="text-zinc-500">Concentration:</span>{' '}
                <span className="font-[family-name:'IBM_Plex_Mono'] text-slate-300">
                  {pos.tickUpper - pos.tickLower <= 120 ? 'JIT-like' : pos.tickUpper - pos.tickLower <= 1200 ? 'Concentrated' : 'Wide/Full range'}
                </span>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
