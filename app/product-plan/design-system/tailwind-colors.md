# ThetaSwap Tailwind Color Reference

## Color Roles

| Role | Tailwind Class | Hex | Usage |
|------|---------------|-----|-------|
| Body background | `bg-zinc-950` | #09090b | Root `<div>` background |
| Panel background | `bg-zinc-900` | #18181b | Sidebar, top bar, table headers, cards |
| Border | `border-zinc-800` | #27272a | All structural borders |
| Elevated border | `border-zinc-700` | #3f3f46 | Input borders, button borders |
| Primary text | `text-slate-200` | #e2e8f0 | Main content text, pool names |
| Secondary text | `text-slate-400` | #94a3b8 | Muted labels, secondary values |
| Muted text | `text-zinc-500` | #71717a | Column headers, metadata |
| Disabled text | `text-zinc-600` | #52525b | Separators, inactive elements |

## Severity Scale (Delta-plus)

| Range | Text Class | Stroke Hex | Condition |
|-------|-----------|-----------|-----------|
| < 0.2 | `text-slate-400` | #94a3b8 | Low concentration (competitive) |
| 0.2 - 0.5 | `text-amber-400` | #fbbf24 | Moderate concentration |
| 0.5 - 0.8 | `text-orange-400` | #fb923c | High concentration |
| > 0.8 | `text-red-400` | #f87171 | Extreme concentration |

## Interactive States

| State | Classes |
|-------|---------|
| Active nav item | `bg-amber-500/10 text-amber-500` |
| Nav item hover | `hover:bg-zinc-800 hover:text-slate-200` |
| Active indicator bar | `bg-amber-500` (3px wide, left side) |
| Row hover | `hover:bg-zinc-800/60` |
| Alternating rows | `bg-zinc-900/50` / `bg-zinc-950` |
| Deposit button | `border-amber-500/40 bg-amber-500/10 text-amber-400` |
| Redeem LONG button | `border-emerald-500/40 bg-emerald-500/10 text-emerald-400` |
| Secondary button | `border-zinc-700 bg-zinc-800 text-slate-400` |
| Wallet hover | `hover:border-amber-500 hover:text-amber-500` |

## Semantic Colors

| Meaning | Text Class | Background |
|---------|-----------|------------|
| Positive P&L | `text-emerald-400` | -- |
| Negative P&L | `text-red-400` | -- |
| Active vault badge | `text-amber-400` | `bg-amber-500/15` |
| Settled vault badge | `text-slate-300` | `bg-slate-600/40` |
| No vault | `text-zinc-500` | `bg-zinc-800` |
| Network online | -- | `bg-emerald-500` (dot) |
