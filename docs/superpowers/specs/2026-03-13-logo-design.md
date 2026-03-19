# ThetaSwap Logomark Design Specification

**Date:** 2026-03-13
**Status:** Approved
**Branch:** 004-fci-token-vault (cross-cutting, applies to all branches)

## Overview

A geometric minimalist logomark for ThetaSwap — the fee concentration insurance protocol for Uniswap V4 passive LPs. The mark encodes the protocol's core narrative: two market participants (passive LPs vs. sophisticated agents) held in equilibrium by the protocol, expressed through the Greek letter Theta (Θ) with a power-law distribution curve as a modified crossbar.

## Concept: Split Θ with Power-Law Crossbar

The logomark is a circle split into two half-arcs of different visual weights (bright left = passive LPs, faded right = sophisticated agents). A straight horizontal crossbar spans the diameter, serving as both the Θ identity and the x-axis for a power-law curve that rises from it. The curve peaks on the left (fairness) and decays towards the right (tail risk), echoing the protocol's α=2 power-squared payoff function.

### Semantic Mapping

| Element | Represents | Visual Treatment |
|---------|-----------|-----------------|
| Left half-arc | Passive LPs (protected) | Full opacity foreground |
| Right half-arc | Sophisticated agents (JIT/MEV) | Stone-400 at 50% opacity |
| Straight crossbar | Θ identity + x-axis | Foreground at 40% opacity |
| Power-law curve | Distribution biased towards fairness / protection threshold | Lime accent, full opacity |

## Core Geometry

- **ViewBox:** 120×120 units
- **Center:** (60, 60)
- **Circle radius:** 33 units
- **Left half-arc:** `M60,27 A33,33 0 0,0 60,93`
- **Right half-arc:** `M60,27 A33,33 0 0,1 60,93`
- **Crossbar:** `x1="27" y1="60" x2="93" y2="60"`
- **Power-law curve:** `M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60`
  - Starts at left edge of crossbar (27, 60)
  - Peak at approximately (43, 36) — ~5 units clearance from the arc boundary at that x-coordinate
  - Decays smoothly back to crossbar at right edge (93, 60)
  - **Must remain fully contained within the circle boundary**

### Stroke Weights by Tier

| Tier | Render Size | Arc Stroke | Crossbar Stroke | Curve Stroke |
|------|------------|------------|-----------------|-------------|
| Hero | 64px+ | 2.5 | 1.5 | 2.5 |
| Nav | 24–48px | 4 | 2.5 | 4 |
| Favicon | 16px | 7 | (dropped) | 7 |
| Token | 32–48px | 4.5 | 2 | 4.5 |

## Color Specification

### Dark Mode (Primary)

| Element | Color | Opacity |
|---------|-------|---------|
| Left arc | `#FAFAF9` (stone-50) | 100% |
| Right arc | `#a8a29e` (stone-400) | 50% |
| Crossbar | `#FAFAF9` (stone-50) | 40% |
| Curve | `#84cc16` (lime-500) | 100% |

### Light Mode

| Element | Color | Opacity |
|---------|-------|---------|
| Left arc | `#1C1917` (stone-900) | 100% |
| Right arc | `#a8a29e` (stone-400) | 50% |
| Crossbar | `#1C1917` (stone-900) | 40% |
| Curve | `#65a30d` (lime-600) | 100% |

Light mode uses lime-600 instead of lime-500 for WCAG AA contrast. Lime-600 (`#65a30d`) achieves ~3.1:1 contrast ratio against white (`#FFFFFF`), meeting WCAG AA for graphical objects (SC 1.4.11, minimum 3:1). Against stone-50 (`#FAFAF9`) the ratio is 2.96:1, marginally below threshold; use white backgrounds for light-mode contexts requiring strict compliance.

### Monochrome Fallback (Print / Emboss)

| Element | Color | Opacity |
|---------|-------|---------|
| Left arc | Foreground | 100% |
| Right arc | Foreground | 40% |
| Crossbar | Foreground | 35% |
| Curve | Foreground | 100% |

All elements use a single foreground color; opacity alone creates the visual hierarchy. Monochrome opacities are reduced (right arc 40%, crossbar 35%) compared to dark/light modes (50%, 40%) to preserve visual hierarchy when color differentiation is absent.

### Inverted Monochrome

Same as monochrome fallback but with `#FAFAF9` foreground on `#1C1917` background. Includes the straight crossbar for Θ legibility.

## Size Variants

### Hero (64px+)

All 4 elements at standard stroke weights. Full detail — both arcs, crossbar, power-law curve.

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#FAFAF9" stroke-width="2.5"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#a8a29e" stroke-width="2.5" opacity="0.5"/>
  <line x1="27" y1="60" x2="93" y2="60" stroke="#FAFAF9" stroke-width="1.5" opacity="0.4"/>
  <path d="M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60" fill="none" stroke="#84cc16" stroke-width="2.5" stroke-linecap="round"/>
</svg>
```

### Nav (24–48px)

All 4 elements with thicker strokes for legibility.

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#FAFAF9" stroke-width="4"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#a8a29e" stroke-width="4" opacity="0.5"/>
  <line x1="27" y1="60" x2="93" y2="60" stroke="#FAFAF9" stroke-width="2.5" opacity="0.4"/>
  <path d="M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60" fill="none" stroke="#84cc16" stroke-width="4" stroke-linecap="round"/>
</svg>
```

### Favicon (16px)

3 elements — crossbar dropped (curve implies it). Simplified 2-segment cubic bezier curve to avoid sub-pixel artifacts at small render sizes.

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#FAFAF9" stroke-width="7"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#a8a29e" stroke-width="7" opacity="0.5"/>
  <path d="M27,60 C34,48 44,38 54,46 C64,52 80,58 93,60" fill="none" stroke="#84cc16" stroke-width="7" stroke-linecap="round"/>
</svg>
```

### Token Icon (32–48px, circular container)

All 4 elements inside a circular container with stone-800 fill and stone-700 border.

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <circle cx="60" cy="60" r="58" fill="#292524" stroke="#44403c" stroke-width="2"/>
  <path d="M60,32 A28,28 0 0,0 60,88" fill="none" stroke="#FAFAF9" stroke-width="4.5"/>
  <path d="M60,32 A28,28 0 0,1 60,88" fill="none" stroke="#a8a29e" stroke-width="4.5" opacity="0.5"/>
  <line x1="32" y1="60" x2="88" y2="60" stroke="#FAFAF9" stroke-width="2" opacity="0.4"/>
  <path d="M32,60 C35,55 38,48 42,43 C45,39 49,38 53,41 C58,46 64,53 71,56 C78,58 84,59 88,60" fill="none" stroke="#84cc16" stroke-width="4.5" stroke-linecap="round"/>
</svg>
```

## Constraints

1. The power-law curve must remain fully contained within the circle boundary at all sizes.
2. The curve starts and ends on the crossbar (the x-axis) — it rises from it and returns to it.
3. At favicon size (16px), the crossbar is dropped and the curve is simplified to a 2-segment cubic bezier.
4. All SVGs use `stroke-linecap="round"` on the curve only. Arcs and crossbar use default `butt` linecap — round caps on arcs would cause visual overlap at the poles where the two half-arcs meet.
5. No fill on any element — the mark is entirely stroke-based.

## Deliverables

1. **Design spec** — this document
2. **SVG source code** — hand-coded SVGs for all 4 size tiers in dark mode (primary)
3. **Size variants** — simplified favicon and token icon SVGs
4. **Mode variants** — dark + light for all tiers; monochrome + inverted monochrome for hero tier only (other tiers use dark/light exclusively)
5. **Integration-ready files** — static SVGs in `app/public/logo/`, inline SVG React component in `app/src/components/`

## Design System Integration

The logomark uses colors from the existing design system:
- Stone palette: stone-50 (`#FAFAF9`), stone-400 (`#a8a29e`), stone-700 (`#44403c`), stone-800 (`#292524`), stone-900 (`#1C1917`)
- Lime accent: lime-500 (`#84cc16`), lime-600 (`#65a30d`)
- Typography pairing: DM Sans (wordmark, if needed later) + IBM Plex Mono (technical contexts)
- Icon weight: aligns with Lucide React stroke-width conventions
