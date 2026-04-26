# dsquared pi (∂²Π) — Logo Generation Prompt Pack

## 2. Stylistic Variants

### Variant A — Swiss Modernist / Helvetica Rationalism
```
Swiss International Style logo mark, monogram ∂²Π as a single
engineered ligature, partial derivative glyph ligatured into uppercase
Greek Pi, mathematical precision, Neue Haas Grotesk proportions,
pure black on pure white, perfect grid construction, generous Akzidenz
counterforms, no ornament, no color, flat vector, looks like a 1960s
ETH Zurich research institute mark, Josef Müller-Brockmann discipline.
--ar 1:1 --v 6 --style raw --stylize 80
```

### Variant B — Academic Journal Seal / Quant Research Stamp
```
Scholarly emblem for a financial mathematics laboratory, the ligature
∂²Π centered inside a fine single-line circular border or thin square
frame, mark reads like the seal of a research journal or quant society,
pure monochrome black ink on cream paper, letterpress sensibility,
hairline rules, tiny serif tick marks optional, evokes Annals of
Applied Probability or the Courant Institute masthead, timeless
academic typography, flat vector, no textures.
--ar 1:1 --v 6 --style raw --stylize 120
```

### Variant C — Minimal Monoline / Contemporary Lab Brand
```
Ultra-minimal monoline logo, ∂²Π drawn as a single continuous uniform
stroke weight, the curve of ∂ flowing seamlessly into the geometric
arches of Π, feels drawn in one gesture, quiet confidence, negative
space dominant, inspired by Apple, Linear, Stripe, and Vercel brand
marks, perfect for a favicon, flat black on white, optional
single-pixel graphite underscore beneath the Π as subtle accent,
vector, no effects.
--ar 1:1 --v 6 --style raw --stylize 60
```

### Variant D (bonus) — Constructed / Grid-Exposed
```
Constructivist logo reveal of the ∂²Π monogram, mark rendered in solid
black over a faint 1px gray construction grid with circle and square
guides, shows the geometric DNA of the letterforms, like a brand
guideline page by Massimo Vignelli or Unimark, flat vector, precise,
monochrome with a single graphite accent, no photorealism.
--ar 1:1 --v 6 --style raw --stylize 100
```

---

## 1. Primary Prompt (paste-ready, ~230 words)

```
Minimal geometric monogram logo for a quantitative research laboratory,
composite typographic mark combining the mathematical glyph for partial
derivative — a stylized lowercase cursive ∂ (partial/del) — with a small
numeral "2" as a precise superscript at its upper right, fused directly
into an uppercase Greek capital Pi (Π) so the right vertical stem of the
∂ flows into or kisses the left vertical leg of the Π, creating one
unified ligature rather than three separate characters. The mark reads
as ∂²Π but feels like a single engineered glyph. Rendered in flat
monochrome black ink on a clean off-white background, single weight
precision strokes with optically corrected joins, subtle contrast
between the calligraphic curve of ∂ and the rigid geometric verticals
of Π, generous negative space, perfectly balanced on a square artboard.
Vector logo design, flat two-dimensional, no gradients, no bevels, no
drop shadows, no photorealism, no texture. Neo-grotesque mathematical
typography inspired by Neue Haas Grotesk, Swiss International Style
poster composition, the visual rigor of an academic journal masthead,
the quiet confidence of a hedge fund research note header. Centered
on a 1:1 canvas with ample margin, crisp vector edges, pixel-perfect
at favicon scale. Accent color option: a single restrained ink
(deep oxblood, graphite navy, or burnt ochre) used only as a tiny
superscript dot or underline. Professional identity design, brand mark
sheet presentation, solid white seamless background.

--ar 1:1 --v 6 --style raw --stylize 150 --chaos 0 --quality 2
```

Best platforms: Midjourney v6.1, Flux 1.1 Pro, Ideogram v2 (Ideogram handles the literal ∂²Π glyph most reliably; Midjourney interprets loosely and often produces a more designed mark).

---

## 3. Negative Prompt / Things to Avoid

```
blockchain cubes, crypto coins, bitcoin symbol, ethereum logo,
abstract swoosh, infinity loop, generic fintech arrow, gradient mesh,
3D bevel, chrome finish, metallic, drop shadow, glow, lens flare,
photorealistic, stock vector clipart, mascot, cartoon character,
human figure, eye symbol, atom icon, DNA helix, circuit board,
neural network lines, rainbow colors, neon, cyberpunk, futuristic,
holographic, glitch, noise texture, grunge, watercolor, hand-drawn
sketch look, low resolution, jpeg artifacts, pixelation, banner with
tagline, extra text, the word "Abrigo", the word "lab", misspelled
Greek letters, lowercase pi instead of capital Pi, roman P instead
of Greek Π, missing superscript 2, three disconnected characters
floating apart
```

Midjourney one-liner:
```
--no crypto, blockchain, swoosh, gradient, bevel, 3d, shadow, photo,
texture, mascot, color, neon, tagline, Abrigo
```

---

## 4. Aspect Ratios & Parameters

| Use case | Aspect | Parameters |
|---|---|---|
| Master mark / brand sheet | `--ar 1:1` | `--v 6 --style raw --stylize 150 --q 2` |
| Horizontal lockup (mark + wordmark) | `--ar 3:1` | `--v 6 --style raw --stylize 100` |
| Favicon / app icon test | `--ar 1:1` | `--v 6 --style raw --stylize 50 --q 2` |
| Signage / letterhead mock | `--ar 16:9` | `--v 6 --style raw --stylize 120` |
| Social avatar | `--ar 1:1` | `--v 6 --style raw --stylize 100` |

Platform notes:
- Midjourney v6.1: `--style raw` strips the painterly bias (essential for logos). `--chaos 0` for deterministic variants.
- Flux 1.1 Pro: drop all `--` params; renders typographic ligatures more literally than MJ.
- Ideogram v2: best for the literal `∂²Π` glyph — prefix prompt with `Typography: ∂²Π`.
- DALL·E 3: prose only, append "Present as a single square logo on white." Expect 3–5 regenerations for Greek glyphs.
- SDXL / Flux-dev local: pair with a typographic LoRA (`logo-redmond`, `vector-illustration`) at 0.6–0.8.

Wordmark pairings (for the human designer on the lockup):
- Primary: Neue Haas Grotesk Display or Söhne (Klim).
- Alternative: GT America Mono for technical contexts.
- Editorial accent: Tiempos Text (Klim) for long-form research publications.

Color system:
- Primary: `#0A0A0A` on `#FAFAF7`.
- Inverse: `#FAFAF7` on `#0A0A0A`.
- Accent (≤5% of surface): `#6E1A1A` oxblood, `#1C2733` graphite navy, or `#8B5A2B` burnt ochre.

---

## 5. Rationale — why these visual choices fit the brand

- Ligatured monogram, not two glyphs: ∂²Π is conceptually one operator (second partial of payoff), so the mark must read as one thing. The ligature enforces the semantic unity — curvature of Π — that the name puns on.
- Calligraphic ∂ vs. geometric Π: the partial-derivative glyph is cursive and analytical; the capital Pi is architectural and structural. Holding both in tension visually encodes the brand's dual nature — rigorous analysis applied to structural payoffs.
- Swiss / neo-grotesque idiom, not fintech: the brand is a laboratory, not a trading app. Visual lineage is ETH Zürich, Courant, RAND, Bell Labs — institutions of thought. This deliberately rejects the crypto/fintech aesthetic.
- Monochrome-first with a single restrained accent: research labs signal credibility through restraint. A single ink (oxblood / graphite navy / ochre) ages well and distances the brand from gradient-heavy Web3.
- Favicon-grade geometry: Abrigo and future sub-products inherit visual equity from this mark, so it must survive at 16×16 px. Single-weight strokes, generous counters, no ornament — the same discipline that lets Bloomberg, Linear, and Vercel work at every size.

---

## 6. Iteration recipe
1. Run Primary Prompt 4× on Midjourney — keep the 1–2 closest to a true ligature.
2. Run Variant A (Swiss) and Variant C (Monoline) 4× each — most likely to yield a usable mark.
3. Take the best output into Ideogram or Flux with the literal `∂²Π` in the prompt to sharpen glyph fidelity.
4. Hand the strongest 2–3 outputs to a vector designer to rebuild cleanly in Illustrator/Figma on a geometric grid. AI output is reference, not final art — the production mark must be hand-constructed for trademark and scalability.
