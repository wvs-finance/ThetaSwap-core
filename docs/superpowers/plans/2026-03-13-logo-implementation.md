# ThetaSwap Logomark Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the ThetaSwap Split Θ logomark as SVG assets, a React component, and integrate it into the frontend app.

**Architecture:** Static SVG files for each size variant and color mode, a single React `<ThetaLogo>` component that selects the right variant based on props, favicon generation, and integration into the app header/footer.

**Tech Stack:** SVG, React + TypeScript, Vite (favicon), Tailwind CSS v4

**Spec:** `docs/superpowers/specs/2026-03-13-logo-design.md`

---

## File Structure

```
app/
├── public/
│   ├── favicon.svg                          # Favicon (dark mode, simplified)
│   └── logo/
│       ├── thetaswap-hero-dark.svg          # Hero tier, dark mode
│       ├── thetaswap-hero-light.svg         # Hero tier, light mode
│       ├── thetaswap-hero-mono.svg          # Hero tier, monochrome (dark fg on white)
│       ├── thetaswap-hero-mono-inv.svg      # Hero tier, inverted mono (light fg on dark)
│       ├── thetaswap-nav-dark.svg           # Nav tier, dark mode
│       ├── thetaswap-nav-light.svg          # Nav tier, light mode
│       ├── thetaswap-favicon-dark.svg       # Favicon tier, dark mode
│       ├── thetaswap-favicon-light.svg      # Favicon tier, light mode
│       ├── thetaswap-token-dark.svg         # Token tier, dark mode
│       └── thetaswap-token-light.svg        # Token tier, light mode
├── src/
│   ├── components/
│   │   └── ThetaLogo.tsx                    # React component
│   └── components/AppLayout.tsx             # Modified: replace Layers icon with ThetaLogo
└── index.html                               # Modified: update favicon link
```

---

## Chunk 1: SVG Asset Files

### Task 1: Create Hero Dark SVG

**Files:**
- Create: `app/public/logo/thetaswap-hero-dark.svg`

- [ ] **Step 1: Create the logo directory**

```bash
mkdir -p app/public/logo
```

- [ ] **Step 2: Write the hero dark SVG**

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#FAFAF9" stroke-width="2.5"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#a8a29e" stroke-width="2.5" opacity="0.5"/>
  <line x1="27" y1="60" x2="93" y2="60" stroke="#FAFAF9" stroke-width="1.5" opacity="0.4"/>
  <path d="M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60" fill="none" stroke="#84cc16" stroke-width="2.5" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 3: Verify SVG renders correctly**

Open `app/public/logo/thetaswap-hero-dark.svg` in a browser. Confirm:
- Circle split into bright left arc and faded right arc
- Straight crossbar at 40% opacity
- Lime power-law curve contained within circle, peaking left

- [ ] **Step 4: Commit**

```bash
git add app/public/logo/thetaswap-hero-dark.svg
git commit -m "feat(logo): add hero dark SVG asset"
```

### Task 2: Create Remaining Hero Mode Variants

**Files:**
- Create: `app/public/logo/thetaswap-hero-light.svg`
- Create: `app/public/logo/thetaswap-hero-mono.svg`
- Create: `app/public/logo/thetaswap-hero-mono-inv.svg`

- [ ] **Step 1: Write hero light SVG**

Same geometry as hero dark. Color changes per spec:
- Left arc: `#1C1917` 100%
- Right arc: `#a8a29e` 50%
- Crossbar: `#1C1917` 40%
- Curve: `#65a30d` 100%

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#1C1917" stroke-width="2.5"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#a8a29e" stroke-width="2.5" opacity="0.5"/>
  <line x1="27" y1="60" x2="93" y2="60" stroke="#1C1917" stroke-width="1.5" opacity="0.4"/>
  <path d="M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60" fill="none" stroke="#65a30d" stroke-width="2.5" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 2: Write hero monochrome SVG**

All elements `#1C1917`. Right arc 40%, crossbar 35%, curve 100%.

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#1C1917" stroke-width="2.5"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#1C1917" stroke-width="2.5" opacity="0.4"/>
  <line x1="27" y1="60" x2="93" y2="60" stroke="#1C1917" stroke-width="1.5" opacity="0.35"/>
  <path d="M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60" fill="none" stroke="#1C1917" stroke-width="2.5" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 3: Write hero inverted monochrome SVG**

All elements `#FAFAF9`. Same opacities as monochrome.

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#FAFAF9" stroke-width="2.5"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#FAFAF9" stroke-width="2.5" opacity="0.4"/>
  <line x1="27" y1="60" x2="93" y2="60" stroke="#FAFAF9" stroke-width="1.5" opacity="0.35"/>
  <path d="M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60" fill="none" stroke="#FAFAF9" stroke-width="2.5" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 4: Verify all three render correctly in browser**

- [ ] **Step 5: Commit**

```bash
git add app/public/logo/thetaswap-hero-light.svg app/public/logo/thetaswap-hero-mono.svg app/public/logo/thetaswap-hero-mono-inv.svg
git commit -m "feat(logo): add hero light, mono, and inverted mono SVG variants"
```

### Task 3: Create Nav Tier SVGs

**Files:**
- Create: `app/public/logo/thetaswap-nav-dark.svg`
- Create: `app/public/logo/thetaswap-nav-light.svg`

- [ ] **Step 1: Write nav dark SVG**

Same geometry, thicker strokes: arc=4, crossbar=2.5, curve=4.

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#FAFAF9" stroke-width="4"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#a8a29e" stroke-width="4" opacity="0.5"/>
  <line x1="27" y1="60" x2="93" y2="60" stroke="#FAFAF9" stroke-width="2.5" opacity="0.4"/>
  <path d="M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60" fill="none" stroke="#84cc16" stroke-width="4" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 2: Write nav light SVG**

Same geometry, light mode colors (stone-900 + lime-600).

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#1C1917" stroke-width="4"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#a8a29e" stroke-width="4" opacity="0.5"/>
  <line x1="27" y1="60" x2="93" y2="60" stroke="#1C1917" stroke-width="2.5" opacity="0.4"/>
  <path d="M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60" fill="none" stroke="#65a30d" stroke-width="4" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 3: Commit**

```bash
git add app/public/logo/thetaswap-nav-dark.svg app/public/logo/thetaswap-nav-light.svg
git commit -m "feat(logo): add nav tier SVG assets (dark + light)"
```

### Task 4: Create Favicon Tier SVGs

**Files:**
- Create: `app/public/logo/thetaswap-favicon-dark.svg`
- Create: `app/public/logo/thetaswap-favicon-light.svg`
- Create: `app/public/favicon.svg`

- [ ] **Step 1: Write favicon dark SVG**

3 elements only — no crossbar. Simplified 2-segment curve. Stroke width 7.

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#FAFAF9" stroke-width="7"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#a8a29e" stroke-width="7" opacity="0.5"/>
  <path d="M27,60 C34,48 44,38 54,46 C64,52 80,58 93,60" fill="none" stroke="#84cc16" stroke-width="7" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 2: Write favicon light SVG**

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60,27 A33,33 0 0,0 60,93" fill="none" stroke="#1C1917" stroke-width="7"/>
  <path d="M60,27 A33,33 0 0,1 60,93" fill="none" stroke="#a8a29e" stroke-width="7" opacity="0.5"/>
  <path d="M27,60 C34,48 44,38 54,46 C64,52 80,58 93,60" fill="none" stroke="#65a30d" stroke-width="7" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 3: Copy dark favicon as primary favicon**

```bash
cp app/public/logo/thetaswap-favicon-dark.svg app/public/favicon.svg
```

- [ ] **Step 4: Commit**

```bash
git add app/public/logo/thetaswap-favicon-dark.svg app/public/logo/thetaswap-favicon-light.svg app/public/favicon.svg
git commit -m "feat(logo): add favicon tier SVGs and replace default favicon"
```

### Task 5: Create Token Icon SVGs

**Files:**
- Create: `app/public/logo/thetaswap-token-dark.svg`
- Create: `app/public/logo/thetaswap-token-light.svg`

- [ ] **Step 1: Write token dark SVG**

Circular container (stone-800 fill, stone-700 border), inner mark with r=28.

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <circle cx="60" cy="60" r="58" fill="#292524" stroke="#44403c" stroke-width="2"/>
  <path d="M60,32 A28,28 0 0,0 60,88" fill="none" stroke="#FAFAF9" stroke-width="4.5"/>
  <path d="M60,32 A28,28 0 0,1 60,88" fill="none" stroke="#a8a29e" stroke-width="4.5" opacity="0.5"/>
  <line x1="32" y1="60" x2="88" y2="60" stroke="#FAFAF9" stroke-width="2" opacity="0.4"/>
  <path d="M32,60 C35,55 38,48 42,43 C45,39 49,38 53,41 C58,46 64,53 71,56 C78,58 84,59 88,60" fill="none" stroke="#84cc16" stroke-width="4.5" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 2: Write token light SVG**

```svg
<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <circle cx="60" cy="60" r="58" fill="#FAFAF9" stroke="#a8a29e" stroke-width="2"/>
  <path d="M60,32 A28,28 0 0,0 60,88" fill="none" stroke="#1C1917" stroke-width="4.5"/>
  <path d="M60,32 A28,28 0 0,1 60,88" fill="none" stroke="#a8a29e" stroke-width="4.5" opacity="0.5"/>
  <line x1="32" y1="60" x2="88" y2="60" stroke="#1C1917" stroke-width="2" opacity="0.4"/>
  <path d="M32,60 C35,55 38,48 42,43 C45,39 49,38 53,41 C58,46 64,53 71,56 C78,58 84,59 88,60" fill="none" stroke="#65a30d" stroke-width="4.5" stroke-linecap="round"/>
</svg>
```

- [ ] **Step 3: Commit**

```bash
git add app/public/logo/thetaswap-token-dark.svg app/public/logo/thetaswap-token-light.svg
git commit -m "feat(logo): add token icon SVG assets (dark + light)"
```

---

## Chunk 2: React Component + App Integration

### Task 6: Create ThetaLogo React Component

**Files:**
- Create: `app/src/components/ThetaLogo.tsx`

- [ ] **Step 1: Write the ThetaLogo component**

An inline SVG component that renders the correct variant based on `size` prop and auto-detects dark/light mode. Uses `currentColor` approach where possible, falling back to explicit colors for the multi-tone elements.

```tsx
interface ThetaLogoProps {
  /** Size tier determines stroke weights and element inclusion */
  size?: 'hero' | 'nav' | 'favicon' | 'token'
  /** Override width/height in pixels */
  className?: string
  /** Accessible label — if omitted, logo is treated as decorative (aria-hidden) */
  ariaLabel?: string
}

export function ThetaLogo({ size = 'nav', className, ariaLabel }: ThetaLogoProps) {
  // Stroke weights per tier (from spec)
  const strokes = {
    hero: { arc: 2.5, crossbar: 1.5, curve: 2.5 },
    nav: { arc: 4, crossbar: 2.5, curve: 4 },
    favicon: { arc: 7, crossbar: 0, curve: 7 },
    token: { arc: 4.5, crossbar: 2, curve: 4.5 },
  }

  const s = strokes[size]
  const showCrossbar = size !== 'favicon'

  // Accessibility: decorative by default, semantic when ariaLabel provided
  const a11yProps = ariaLabel
    ? { role: 'img' as const, 'aria-label': ariaLabel }
    : { 'aria-hidden': true as const }

  // Favicon uses simplified curve path
  const curvePath =
    size === 'favicon'
      ? 'M27,60 C34,48 44,38 54,46 C64,52 80,58 93,60'
      : 'M27,60 C30,55 33,46 37,40 C40,36 44,35 48,38 C53,43 59,52 66,55 C73,57 82,59 93,60'

  if (size === 'token') {
    return (
      <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} {...a11yProps}>
        <circle cx="60" cy="60" r="58" className="fill-stone-50 dark:fill-stone-800 stroke-stone-400 dark:stroke-stone-700" strokeWidth="2" />
        <path d="M60,32 A28,28 0 0,0 60,88" fill="none" className="stroke-stone-900 dark:stroke-stone-50" strokeWidth={s.arc} />
        <path d="M60,32 A28,28 0 0,1 60,88" fill="none" stroke="#a8a29e" strokeWidth={s.arc} opacity="0.5" />
        <line x1="32" y1="60" x2="88" y2="60" className="stroke-stone-900 dark:stroke-stone-50" strokeWidth={s.crossbar} opacity="0.4" />
        <path
          d="M32,60 C35,55 38,48 42,43 C45,39 49,38 53,41 C58,46 64,53 71,56 C78,58 84,59 88,60"
          fill="none"
          className="stroke-lime-600 dark:stroke-lime-500"
          strokeWidth={s.curve}
          strokeLinecap="round"
        />
      </svg>
    )
  }

  return (
    <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} {...a11yProps}>
      {/* Left arc — passive LPs (bright) */}
      <path
        d="M60,27 A33,33 0 0,0 60,93"
        fill="none"
        className="stroke-stone-900 dark:stroke-stone-50"
        strokeWidth={s.arc}
      />
      {/* Right arc — sophisticated agents (faded) */}
      <path
        d="M60,27 A33,33 0 0,1 60,93"
        fill="none"
        stroke="#a8a29e"
        strokeWidth={s.arc}
        opacity="0.5"
      />
      {/* Crossbar — Θ identity + x-axis */}
      {showCrossbar && (
        <line
          x1="27" y1="60" x2="93" y2="60"
          className="stroke-stone-900 dark:stroke-stone-50"
          strokeWidth={s.crossbar}
          opacity="0.4"
        />
      )}
      {/* Power-law curve — distribution / protection threshold */}
      <path
        d={curvePath}
        fill="none"
        className="stroke-lime-600 dark:stroke-lime-500"
        strokeWidth={s.curve}
        strokeLinecap="round"
      />
    </svg>
  )
}
```

- [ ] **Step 2: Verify component renders in dev server**

```bash
cd app && npm run dev
```

Import `<ThetaLogo size="hero" className="w-32 h-32" />` temporarily in any page to verify render.

- [ ] **Step 3: Commit**

```bash
git add app/src/components/ThetaLogo.tsx
git commit -m "feat(logo): add ThetaLogo React component with size tiers and dark/light mode"
```

### Task 7: Integrate Logo into App Header

**Files:**
- Modify: `app/src/components/AppLayout.tsx:3` (remove Layers import)
- Modify: `app/src/components/AppLayout.tsx:91-103` (replace footer logo)

- [ ] **Step 1: Add ThetaLogo import to AppLayout**

Replace the `Layers` import with `ThetaLogo`:

```tsx
// Remove: import { Layers, ArrowLeft } from 'lucide-react'
// Add:
import { ArrowLeft } from 'lucide-react'
import { ThetaLogo } from './ThetaLogo'
```

- [ ] **Step 2: Replace footer Layers icon with ThetaLogo**

In the footer section (~line 91-103), replace the Design OS branding with ThetaSwap:

```tsx
{/* Footer with logo */}
<footer className="py-8 flex justify-center">
  <div className="flex items-center gap-2 text-stone-400 dark:text-stone-500">
    <ThetaLogo size="nav" className="w-5 h-5" />
    <span className="text-xs font-medium tracking-tight">ThetaSwap</span>
  </div>
</footer>
```

- [ ] **Step 3: Verify in dev server**

```bash
cd app && npm run dev
```

Confirm footer shows the ThetaLogo mark + "ThetaSwap" text. Toggle dark/light mode to verify both render correctly.

- [ ] **Step 4: Commit**

```bash
git add app/src/components/AppLayout.tsx
git commit -m "feat(logo): integrate ThetaLogo into app footer, replace Design OS branding"
```

### Task 8: Update Favicon in index.html

**Files:**
- Modify: `app/index.html`

- [ ] **Step 1: Update favicon link tag**

Find the existing `<link rel="icon"` tag and replace:

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
```

- [ ] **Step 2: Update page title**

```html
<title>ThetaSwap</title>
```

- [ ] **Step 3: Verify favicon appears in browser tab**

```bash
cd app && npm run dev
```

Open the app and confirm the favicon shows the simplified split-theta mark with lime curve.

- [ ] **Step 4: Commit**

```bash
git add app/index.html
git commit -m "feat(logo): update favicon and page title to ThetaSwap"
```

### Task 9: Remove Old Assets

**Files:**
- Delete: `app/public/vite.svg`
- Delete: `app/src/assets/react.svg`

- [ ] **Step 1: Check if old assets are imported anywhere**

```bash
grep -r "vite.svg\|react.svg" app/src/ app/index.html
```

If referenced, remove those references first.

- [ ] **Step 2: Delete old assets**

```bash
rm app/public/vite.svg app/src/assets/react.svg
```

- [ ] **Step 3: Verify app still builds**

```bash
cd app && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 4: Commit**

```bash
git add -u app/public/vite.svg app/src/assets/react.svg
git commit -m "chore(logo): remove default Vite and React SVG assets"
```

### Task 10: Final Verification

- [ ] **Step 1: Run dev server and verify all logo placements**

```bash
cd app && npm run dev
```

Check:
- [ ] Favicon in browser tab (split theta + lime curve)
- [ ] Footer logo (nav size ThetaLogo + "ThetaSwap" text)
- [ ] Dark mode renders correctly (stone-50 arcs + lime-500 curve)
- [ ] Light mode renders correctly (stone-900 arcs + lime-600 curve)

- [ ] **Step 2: Run production build**

```bash
cd app && npm run build
```

Expected: Build succeeds with no warnings.

- [ ] **Step 3: Verify all SVG files exist**

```bash
ls -la app/public/logo/ app/public/favicon.svg
```

Expected: 10 SVG files in `logo/` + `favicon.svg`.
