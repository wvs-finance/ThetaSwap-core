# ThetaSwap Font Configuration

## Font Families

| Role | Font | Weights | Usage |
|------|------|---------|-------|
| Heading | Instrument Serif | Regular, Italic | Logo ("ThetaSwap"), section headings, stat card labels |
| Body | IBM Plex Sans | 400, 500, 600 | Navigation labels, body text, column headers, descriptions |
| Mono | IBM Plex Mono | 400, 500, 600 | ALL numeric values, addresses, code, badges |

## Google Fonts Import

Add to `<head>` in `index.html`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet" />
```

## Tailwind Usage

In Tailwind CSS, use the `font-[family-name:...]` utility:

```html
<!-- Headings -->
<h1 class="font-[family-name:'Instrument_Serif'] italic">ThetaSwap</h1>

<!-- Body text -->
<p class="font-[family-name:'IBM_Plex_Sans']">Navigation label</p>

<!-- Numeric values (ALWAYS use this for numbers) -->
<span class="font-[family-name:'IBM_Plex_Mono'] tabular-nums">0.72</span>
```

## Important Rules

1. **All numeric values** must use IBM Plex Mono with `tabular-nums` for proper alignment in tables
2. **Section headings** use Instrument Serif italic (e.g., "Positions", "Oracle State", "Vault")
3. **Logo** uses Instrument Serif italic: full "ThetaSwap" when expanded, "T" when sidebar collapsed
4. **Column headers** use IBM Plex Sans in `text-xs font-medium uppercase tracking-wider`
5. **Research section** uses Instrument Serif for article headings with `IBM_Plex_Mono` section numbers (e.g., "section-1")

## SVG Font Usage

For text inside SVG charts, use `fontFamily` prop:

```tsx
<text fontFamily="'IBM Plex Mono', monospace" fontSize={8}>0.25</text>
<text fontFamily="'IBM Plex Sans', sans-serif" fontSize={8}>Delta-plus</text>
```
