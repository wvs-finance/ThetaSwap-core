import { useRef, useEffect } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import type {
  ResearchProps,
  WelfareComparison,
  DeltaDistBin,
  PayoffSensitivityPoint,
  CalibrationParameter,
} from '@/../product/sections/research/types'

// ---------------------------------------------------------------------------
// LaTeX rendering
// ---------------------------------------------------------------------------

function Tex({ math, display = false }: { math: string; display?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    if (ref.current) {
      katex.render(math, ref.current, {
        displayMode: display,
        throwOnError: false,
        trust: true,
      })
    }
  }, [math, display])
  return <span ref={ref} />
}

// ---------------------------------------------------------------------------
// Welfare Bar Chart (SVG)
// ---------------------------------------------------------------------------

function WelfareChart({ data }: { data: WelfareComparison[] }) {
  const W = 480
  const H = 200
  const pad = { top: 16, right: 20, bottom: 40, left: 60 }
  const cw = W - pad.left - pad.right
  const ch = H - pad.top - pad.bottom

  const vals = data.map((d) => d.mean)
  const vMin = Math.min(...vals) * 1.3
  const vMax = Math.max(...vals, 0) * 1.1
  const vRange = vMax - vMin || 1

  const barWidth = cw / data.length - 8
  const vy = (v: number) => pad.top + (1 - (v - vMin) / vRange) * ch
  const zeroY = vy(0)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 240 }}>
      {/* Zero line */}
      <line x1={pad.left} y1={zeroY} x2={W - pad.right} y2={zeroY} stroke="#52525b" strokeWidth={0.5} />

      {/* Bars */}
      {data.map((d, i) => {
        const bx = pad.left + (i * cw) / data.length + 4
        const by = vy(d.mean)
        const bh = Math.abs(zeroY - by)
        const isNeg = d.mean < 0
        const color = i === 0 ? '#ef4444' : '#fbbf24'
        return (
          <g key={d.label}>
            <rect
              x={bx}
              y={isNeg ? zeroY : by}
              width={barWidth}
              height={bh}
              fill={color}
              fillOpacity={0.7}
              rx={1}
            />
            {/* Error bar (std) */}
            <line
              x1={bx + barWidth / 2}
              y1={vy(d.mean - d.std)}
              x2={bx + barWidth / 2}
              y2={vy(d.mean + d.std)}
              stroke={color}
              strokeWidth={1}
              strokeOpacity={0.5}
            />
            {/* Cap lines */}
            <line x1={bx + barWidth / 2 - 4} y1={vy(d.mean - d.std)} x2={bx + barWidth / 2 + 4} y2={vy(d.mean - d.std)} stroke={color} strokeWidth={1} strokeOpacity={0.5} />
            <line x1={bx + barWidth / 2 - 4} y1={vy(d.mean + d.std)} x2={bx + barWidth / 2 + 4} y2={vy(d.mean + d.std)} stroke={color} strokeWidth={1} strokeOpacity={0.5} />
            {/* Label */}
            <text
              x={bx + barWidth / 2}
              y={H - pad.bottom + 14}
              textAnchor="middle"
              fontSize={8}
              fontFamily="'IBM Plex Mono', monospace"
              className="fill-zinc-400"
            >
              {d.label}
            </text>
          </g>
        )
      })}

      {/* Y-axis */}
      {[-0.06, -0.04, -0.02, 0].map((t) => (
        <text
          key={t}
          x={pad.left - 6}
          y={vy(t) + 3}
          textAnchor="end"
          fontSize={8}
          fontFamily="'IBM Plex Mono', monospace"
          className="fill-zinc-500"
        >
          {t.toFixed(2)}
        </text>
      ))}

      <text
        x={pad.left - 40}
        y={H / 2}
        textAnchor="middle"
        fontSize={8}
        fontFamily="'IBM Plex Sans', sans-serif"
        className="fill-zinc-500"
        transform={`rotate(-90, ${pad.left - 40}, ${H / 2})`}
      >
        Welfare (Δ fee revenue)
      </text>
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Δ⁺ Distribution Histogram (SVG)
// ---------------------------------------------------------------------------

function DistributionChart({ data }: { data: DeltaDistBin[] }) {
  const W = 480
  const H = 180
  const pad = { top: 12, right: 20, bottom: 36, left: 40 }
  const cw = W - pad.left - pad.right
  const ch = H - pad.top - pad.bottom

  const maxCount = Math.max(...data.map((d) => d.count))
  const barWidth = cw / data.length - 2

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 220 }}>
      {data.map((d, i) => {
        const bx = pad.left + (i * cw) / data.length + 1
        const bh = (d.count / maxCount) * ch
        const by = pad.top + ch - bh
        // Color gradient: low = zinc, high = amber/red
        const ratio = i / (data.length - 1)
        const color = ratio < 0.3 ? '#71717a' : ratio < 0.6 ? '#fbbf24' : ratio < 0.8 ? '#fb923c' : '#f87171'
        return (
          <g key={d.bin}>
            <rect x={bx} y={by} width={barWidth} height={bh} fill={color} fillOpacity={0.7} rx={1} />
            <text
              x={bx + barWidth / 2}
              y={by - 3}
              textAnchor="middle"
              fontSize={7}
              fontFamily="'IBM Plex Mono', monospace"
              className="fill-zinc-500"
            >
              {d.count}
            </text>
            <text
              x={bx + barWidth / 2}
              y={H - pad.bottom + 12}
              textAnchor="middle"
              fontSize={7}
              fontFamily="'IBM Plex Mono', monospace"
              className="fill-zinc-500"
            >
              {d.bin}
            </text>
          </g>
        )
      })}

      <text
        x={W / 2}
        y={H - 4}
        textAnchor="middle"
        fontSize={8}
        fontFamily="'IBM Plex Sans', sans-serif"
        className="fill-zinc-500"
      >
        Δ⁺ Range
      </text>
      <text
        x={pad.left - 24}
        y={H / 2}
        textAnchor="middle"
        fontSize={8}
        fontFamily="'IBM Plex Sans', sans-serif"
        className="fill-zinc-500"
        transform={`rotate(-90, ${pad.left - 24}, ${H / 2})`}
      >
        Epoch Count
      </text>
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Payoff Sensitivity Line Chart (SVG)
// ---------------------------------------------------------------------------

function SensitivityChart({ data }: { data: PayoffSensitivityPoint[] }) {
  const W = 480
  const H = 180
  const pad = { top: 12, right: 20, bottom: 32, left: 48 }
  const cw = W - pad.left - pad.right
  const ch = H - pad.top - pad.bottom

  const xMin = data[0].strike
  const xMax = data[data.length - 1].strike
  const xRange = xMax - xMin || 1
  const yMax = Math.max(...data.map((d) => d.meanPayout)) * 1.1
  const yRange = yMax || 1

  const tx = (s: number) => pad.left + ((s - xMin) / xRange) * cw
  const ty = (p: number) => pad.top + (1 - p / yRange) * ch

  const pathD = data
    .map((pt, i) => `${i === 0 ? 'M' : 'L'}${tx(pt.strike).toFixed(1)},${ty(pt.meanPayout).toFixed(1)}`)
    .join(' ')

  const areaD = `${pathD} L${tx(data[data.length - 1].strike).toFixed(1)},${ty(0).toFixed(1)} L${tx(data[0].strike).toFixed(1)},${ty(0).toFixed(1)} Z`

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 220 }}>
      {/* Grid */}
      {[0, 0.02, 0.04, 0.06, 0.08].map((t) => (
        <line key={t} x1={pad.left} y1={ty(t)} x2={W - pad.right} y2={ty(t)} stroke="#27272a" strokeWidth={0.5} />
      ))}

      <path d={areaD} fill="#fbbf24" fillOpacity={0.06} />
      <path d={pathD} fill="none" stroke="#fbbf24" strokeWidth={1.5} strokeLinejoin="round" />

      {/* Data points */}
      {data.map((pt) => (
        <circle key={pt.strike} cx={tx(pt.strike)} cy={ty(pt.meanPayout)} r={2.5} fill="#fbbf24" stroke="#18181b" strokeWidth={1} />
      ))}

      {/* Highlight K=0.25 */}
      <line x1={tx(0.25)} y1={pad.top} x2={tx(0.25)} y2={H - pad.bottom} stroke="#94a3b8" strokeWidth={1} strokeDasharray="3,3" />
      <text x={tx(0.25) + 4} y={pad.top + 10} fontSize={7} fontFamily="'IBM Plex Mono', monospace" className="fill-slate-400">
        K=0.25
      </text>

      {/* X labels */}
      {data.filter((_, i) => i % 2 === 0).map((pt) => (
        <text key={pt.strike} x={tx(pt.strike)} y={H - pad.bottom + 12} textAnchor="middle" fontSize={8} fontFamily="'IBM Plex Mono', monospace" className="fill-zinc-500">
          {pt.strike.toFixed(2)}
        </text>
      ))}

      {/* Y labels */}
      {[0, 0.02, 0.04, 0.06, 0.08].map((t) => (
        <text key={t} x={pad.left - 4} y={ty(t) + 3} textAnchor="end" fontSize={8} fontFamily="'IBM Plex Mono', monospace" className="fill-zinc-500">
          {t.toFixed(2)}
        </text>
      ))}

      <text x={W / 2} y={H - 4} textAnchor="middle" fontSize={8} fontFamily="'IBM Plex Sans', sans-serif" className="fill-zinc-500">
        Strike (K)
      </text>
      <text x={pad.left - 32} y={H / 2} textAnchor="middle" fontSize={8} fontFamily="'IBM Plex Sans', sans-serif" className="fill-zinc-500" transform={`rotate(-90, ${pad.left - 32}, ${H / 2})`}>
        Mean Payout
      </text>
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Parameter Table
// ---------------------------------------------------------------------------

function ParameterTable({ params }: { params: CalibrationParameter[] }) {
  return (
    <table className="w-full border-collapse">
      <thead className="border-b border-zinc-700">
        <tr>
          <th className="px-4 py-2.5 text-left font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
            Parameter
          </th>
          <th className="px-4 py-2.5 text-right font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
            Value
          </th>
          <th className="px-4 py-2.5 text-left font-[family-name:'IBM_Plex_Sans'] text-xs font-medium uppercase tracking-wider text-slate-500">
            Description
          </th>
        </tr>
      </thead>
      <tbody>
        {params.map((p, i) => (
          <tr
            key={p.name}
            className={`border-b border-zinc-800/50 ${i % 2 === 0 ? 'bg-zinc-900/30' : ''}`}
          >
            <td className="px-4 py-2.5 text-sm text-amber-400">
              <ParamName name={p.name} />
            </td>
            <td className="px-4 py-2.5 text-right font-[family-name:'IBM_Plex_Mono'] text-sm tabular-nums text-slate-200">
              {p.value}
            </td>
            <td className="px-4 py-2.5 font-[family-name:'IBM_Plex_Sans'] text-sm text-slate-400">
              {p.description}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function Research({
  title,
  abstract,
  methodology,
  results,
  parameters,
  conclusion,
}: ResearchProps) {
  return (
    <div className="min-h-full bg-zinc-950 text-slate-200">
      <article className="mx-auto max-w-[960px] px-8 py-10 font-[family-name:'IBM_Plex_Sans']">
        {/* Title */}
        <h1 className="mb-2 font-[family-name:'IBM_Plex_Sans'] text-3xl font-semibold text-slate-100">
          {title}
        </h1>
        <p className="mb-8 text-sm text-zinc-500">
          ThetaSwap Research · Backtest Report · ETH-USDC 30bps
        </p>

        <hr className="mb-8 border-zinc-800" />

        {/* §1 Abstract */}
        <section className="mb-10">
          <h2 className="mb-3 font-[family-name:'IBM_Plex_Sans'] text-xl font-semibold text-slate-200">
            <span className="mr-2 font-[family-name:'IBM_Plex_Mono'] text-sm not-italic text-zinc-500">§1</span>
            Abstract
          </h2>
          <p className="leading-relaxed text-slate-300">
            We evaluate the effectiveness of a fee-concentration insurance mechanism for passive
            Uniswap V4 liquidity providers. Using 180 days of mainnet ETH-USDC swap events, we
            simulate the Fee Concentration Index (<Tex math="\Delta^+" />) under epoch-based
            accumulation and compute lookback payoffs for LONG token holders. Our findings show
            that hedged LPs outperform unhedged LPs in 67% of epochs when{' '}
            <Tex math="\Delta^+" /> exceeds the strike threshold, with a mean hedge value of
            $0.034 per dollar deposited.
          </p>

          {/* Summary stats */}
          <div className="mt-4 grid grid-cols-3 gap-4">
            <SummaryStatCard label="Epochs Above Strike" value={`${results.summary.epochsAboveStrike} / ${results.summary.totalEpochs}`} />
            <SummaryStatCard label="% Better Off Hedged" value={`${results.summary.pctBetterOff}%`} />
            <SummaryStatCard label="Mean Hedge Value" value={`$${results.summary.meanHedgeValue.toFixed(3)} / $1`} />
          </div>
        </section>

        {/* §2 Methodology */}
        <section className="mb-10">
          <h2 className="mb-3 font-[family-name:'IBM_Plex_Sans'] text-xl font-semibold text-slate-200">
            <span className="mr-2 font-[family-name:'IBM_Plex_Mono'] text-sm not-italic text-zinc-500">§2</span>
            Methodology
          </h2>

          <h3 className="mb-1 text-sm font-medium uppercase tracking-wider text-zinc-500">Data Source</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">{methodology.dataSource}</p>

          <h3 className="mb-1 text-sm font-medium uppercase tracking-wider text-zinc-500">Mechanism</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            Epoch-based <Tex math="\Delta^+" /> accumulation with destruction-by-abandonment reset.
            Each epoch: <Tex math="\Theta = \sum_{k} \frac{1}{\ell_k}" /> over position removals,{' '}
            <Tex math="A_T = \sqrt{\Theta}" />, <Tex math="\Delta^+ = \max(0,\, A_T - \text{atNull})" />.
          </p>

          <h3 className="mb-1 text-sm font-medium uppercase tracking-wider text-zinc-500">Payoff Function</h3>
          <p className="mb-2 text-sm leading-relaxed text-slate-400">
            Power-squared lookback: the LONG payout is a convex function of the high-water mark (HWM) of{' '}
            <Tex math="\Delta^+" /> within the epoch, relative to the strike <Tex math="K" />.
          </p>

          {/* Formula display */}
          <div className="my-4 rounded-none border border-zinc-800 bg-zinc-900 px-6 py-5 text-center">
            <Tex
              math="p(\text{HWM},\, K) \;=\; \max\!\left(0,\;\left(\frac{\text{HWM} - K}{1 - K}\right)^{\!2}\right)"
              display
            />
          </div>
        </section>

        {/* §3 Results */}
        <section className="mb-10">
          <h2 className="mb-4 font-[family-name:'IBM_Plex_Sans'] text-xl font-semibold text-slate-200">
            <span className="mr-2 font-[family-name:'IBM_Plex_Mono'] text-sm not-italic text-zinc-500">§3</span>
            Results
          </h2>

          {/* Chart 1: Welfare Comparison */}
          <div className="mb-8">
            <h3 className="mb-1 text-sm font-medium text-slate-300">
              Figure 1. Hedged vs Unhedged LP Welfare
            </h3>
            <p className="mb-3 text-xs text-zinc-500">
              Mean change in fee revenue per dollar of liquidity. Error bars: ±1 std dev.
            </p>
            <div className="rounded-none border border-zinc-800 bg-zinc-900/50 p-4">
              <WelfareChart data={results.welfareComparison} />
            </div>
          </div>

          {/* Chart 2: Δ⁺ Distribution */}
          <div className="mb-8">
            <h3 className="mb-1 text-sm font-medium text-slate-300">
              Figure 2. <Tex math="\Delta^+" /> Distribution Across Epochs
            </h3>
            <p className="mb-3 text-xs text-zinc-500">
              Frequency of observed epoch-maximum <Tex math="\Delta^+" /> values. Bars colored by severity.
            </p>
            <div className="rounded-none border border-zinc-800 bg-zinc-900/50 p-4">
              <DistributionChart data={results.deltaDistribution} />
            </div>
          </div>

          {/* Chart 3: Payoff Sensitivity */}
          <div className="mb-8">
            <h3 className="mb-1 text-sm font-medium text-slate-300">
              Figure 3. Payoff Sensitivity to Strike
            </h3>
            <p className="mb-3 text-xs text-zinc-500">
              Mean LONG payout per dollar deposited as a function of strike <Tex math="K" />. Dashed line: <Tex math="K = 0.25" /> (default).
            </p>
            <div className="rounded-none border border-zinc-800 bg-zinc-900/50 p-4">
              <SensitivityChart data={results.payoffSensitivity} />
            </div>
          </div>
        </section>

        {/* §4 Parameters */}
        <section className="mb-10">
          <h2 className="mb-4 font-[family-name:'IBM_Plex_Sans'] text-xl font-semibold text-slate-200">
            <span className="mr-2 font-[family-name:'IBM_Plex_Mono'] text-sm not-italic text-zinc-500">§4</span>
            Calibration Parameters
          </h2>
          <div className="rounded-none border border-zinc-800 bg-zinc-900/50">
            <ParameterTable params={parameters} />
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            See §2, Payoff Function for parameter usage. Values calibrated from ETH-USDC 30bps backtest.
            Conservation: <Tex math="p_{\text{LONG}} + p_{\text{SHORT}} = 1" /> per token pair.
          </p>
        </section>

        {/* §5 Conclusion */}
        <section className="mb-10">
          <h2 className="mb-3 font-[family-name:'IBM_Plex_Sans'] text-xl font-semibold text-slate-200">
            <span className="mr-2 font-[family-name:'IBM_Plex_Mono'] text-sm not-italic text-zinc-500">§5</span>
            Conclusion
          </h2>
          <p className="leading-relaxed text-slate-300">
            Fee concentration insurance is most valuable for pools with moderate-to-high JIT
            activity (<Tex math="\Delta^+ > 0.20" />) and epoch lengths of 1–7 days. The
            power-squared lookback payoff provides convex exposure that rewards hedgers
            proportionally to extraction severity. At <Tex math="K = 0.25" />, 67% of epochs
            produce a positive hedge value, with diminishing returns below{' '}
            <Tex math="K = 0.15" /> due to premium costs exceeding payouts in low-concentration
            epochs.
          </p>
        </section>

        <hr className="mb-4 border-zinc-800" />
        <p className="text-xs text-zinc-600">
          This report is auto-generated from backtest data. It does not constitute financial advice.
          See the full LaTeX specification for formal proofs and extended analysis.
        </p>
      </article>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Summary stat mini-card
// ---------------------------------------------------------------------------

const PARAM_LATEX: Record<string, string> = {
  'γ (gamma)': '\\gamma',
  'α (alpha)': '\\alpha',
  'epochLength': '\\text{epochLength}',
  'K (strike)': 'K \\;(\\text{strike})',
  'atNull₀': '\\text{atNull}_0',
}

function ParamName({ name }: { name: string }) {
  const latex = PARAM_LATEX[name]
  if (latex) return <Tex math={latex} />
  return <span className="font-[family-name:'IBM_Plex_Mono']">{name}</span>
}

function SummaryStatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-none border border-zinc-800 bg-zinc-900 px-4 py-3">
      <div className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</div>
      <div className="mt-1 font-[family-name:'IBM_Plex_Mono'] text-lg tabular-nums text-slate-200">
        {value}
      </div>
    </div>
  )
}
