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
