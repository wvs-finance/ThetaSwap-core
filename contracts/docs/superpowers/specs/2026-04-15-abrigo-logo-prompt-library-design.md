# Abrigo Logo Prompt Library — Design Spec

**Status:** Draft Rev 1
**Date:** 2026-04-15
**Scope:** Design contract for a reusable, 8-variant Midjourney prompt library that produces Abrigo logo and brand-imagery candidates. Covers library structure, visual vocabulary, per-prompt schema, file layout, authorship, and review workflow.
**Out of scope:** generator-tooling (no runtime parameterized generator), DALL-E / Stable Diffusion ports, actual logo selection (library produces candidates; founder selects), the d²π Labs parent-brand logo (covered by the existing `contracts/.scratch/dsquared-pi-logo-prompt.md` and remains separate).

---

## 0. Glossary

- **Abrigo** — the retail-facing sub-brand of d²π Labs. Spanish for *shelter / coat*. See `project_ran_brand_name.md`.
- **Library** — a single markdown file containing eight fully-specified Midjourney prompt variants, each annotated with usage guidance and iteration notes.
- **Variant** — one self-contained prompt block within the library. Each variant has a name, role, usage, full Midjourney prompt with parameters, negative guidance, and iteration notes.
- **Vernacular-shelter vocabulary** — the visual element palette rooted in Latin American shelter forms (terracotta roof tile, interior patio, carved wooden door, woven textile, morning light through arched doorway, overlapping cloth, stitched felt, blanket folds) WITHOUT the "colonial" label or colonial-period specificity.
- **Modern-finance discipline** — the visual rigor palette (clean geometry, single dominant color with neutral, precise sans-serif, negative-space discipline, confident stroke weights) WITHOUT old-bank-seal ornament, security-print texture, certificate borders, or classical columns.
- **Logo type** — one of: *symbol-only mark*, *wordmark*, *combination* (symbol + word), *scene* (brand imagery with word overlaid).
- **Review triad for logo artifacts** — Image Prompt Engineer + Brand Guardian + Cultural Intelligence Strategist. Claim Auditor is not seated because image prompts carry no painkiller claims.
- **Hard cap** — lifecycle rule (spec `2026-04-15-abrigo-branding-agent-design.md` §7.4) that stops a review loop at 5 revisions and escalates to founder.

## 1. Context

The Abrigo brand has a tagline / positioning artifact (graduated, `contracts/.branding/artifacts/taglines.md`) and a named identity (Spanish: shelter/coat). It has no visual identity. When the founder needs a landing-page logo, X avatar, deck cover, app icon, or brand imagery, there is no current protocol for producing it on-brand.

The existing d²π Labs prompt file at `contracts/.scratch/dsquared-pi-logo-prompt.md` covers the parent-brand mark with three variants (Swiss Modernist, Academic Journal Seal, Minimal Monoline). That file is the proof of concept for Midjourney-prompt authorship in this project; it is kept for d²π Labs and not reused for Abrigo because the two brands have intentionally different visual vocabularies (mathematical / academic for d²π Labs; warm / sheltering for Abrigo).

The trigger for this spec is the impending need for Abrigo landing-page imagery and an X avatar tied to the handle creation work already planned.

## 2. Goals

- Produce 8 Midjourney prompt variants covering the full range of concrete Abrigo logo and brand-imagery use-cases (app icon, X avatar, landing hero, deck cover, letterhead, hero imagery).
- Anchor every variant in a hybrid vernacular-shelter + modern-finance visual vocabulary that resonates with the Colombia pilot market without collapsing into colonial-era imperial symbolism or into crypto-finance cliché.
- Provide per-variant usage guidance so the founder knows which variant to deploy on which surface without re-reading the whole library.
- Keep the library reusable — prompts should survive Midjourney version bumps and minor aesthetic drift without needing to be rewritten from scratch.

## 3. Non-Goals

- **No runtime generator tool.** This is a static library, not a dispatchable "give me a prompt" subagent. If a parameterized generator proves useful later, it becomes a separate spec.
- **No DALL-E / Stable Diffusion ports.** Midjourney only, matching the d²π Labs pattern. Manual adaptation is the founder's choice if another tool is needed.
- **No actual logo selection.** The library produces prompt candidates; the founder generates images and picks. The library is not a decision system.
- **No visual identity standards document.** Color palette, typography specimens, spacing rules, and brand guidelines are a downstream artifact that builds on whichever logo variant the founder selects.
- **No d²π Labs content.** The parent-brand mark has its own existing prompt file and is governed separately.

---

## 4. Visual Vocabulary

### 4.1 The hybrid: vernacular-shelter + modern-finance

Every variant draws from two palettes and no others.

**Shelter / vernacular palette** — terracotta clay roof tile, overlapping clay tiles, stitched felt, woven textile pattern, blanket folds, interior patio or courtyard, morning light through arched doorway, carved wooden door, overlapping cloth, warm painted wall (ochre / cerulean / warm cream), single-letter *A* whose counterform evokes an archway or roofline, sheltering gesture like a hand over a small form.

**Modern-finance discipline palette** — clean geometry, single dominant color plus one neutral, precise contemporary sans-serif (humanist or geometric, not display-serif and not "bank serif"), grid construction, generous negative space, confident stroke weight, flat vector language, restrained palette, no ornament.

### 4.2 Explicit bans

Every variant's prompt must explicitly ban all of the following to prevent Midjourney's default drift:

- **Colonial-era specificity.** No "colonial," "Spanish colonial," "baroque," "Victorian," "Classical," "neoclassical," "colonial-period," "19th-century bank," or any period vocabulary that imports imperial symbolism.
- **Crypto / fintech cliché.** No coins, no chains, no padlocks, no shields, no blockchain lattices, no upward-arrows, no dollar signs, no Bitcoin "₿," no "abstract digital currency."
- **Old-bank ornament.** No security-print crosshatching, no certificate borders, no classical columns, no scrollwork, no monogram seals in the ornate Victorian sense, no scroll-banners, no heraldry.
- **Rustic-folk-art texture.** No handcrafted-looking rough edges, no folk-craft naïveté, no "artisan" as a stylistic register. Warm should not equal naïve.
- **Stereotype imagery.** No sombreros, no cacti, no piñatas, no any pan-Latino visual shorthand. Shelter elements must be specific (terracotta tile, not "Latin American architecture").

### 4.3 Cultural-fit discipline

The vocabulary is rooted in Latin American vernacular shelter forms (terracotta roof tile is the most globally-legible anchor) but explicitly NOT labeled "colonial" or tied to the colonial period. Every prompt must pass three reads:

1. Would a Colombian household recognize the shelter element as theirs? (terracotta roof tile, patio, morning light — yes)
2. Does the element carry imperial / colonial symbolism that a decolonial-aware viewer would pattern-match? (colonial-period specifics — no; warm vernacular elements — no)
3. Does the element translate across the mission scope to other underserved-FX countries, even if it doesn't pattern-match exactly? (terracotta roof and overlapping clay tiles exist across Mediterranean, MENA, South Asia; woven textile exists everywhere — yes)

---

## 5. Library Structure

Eight variants across four logo types, two variants per type.

### 5.1 Symbol-only marks (2)

Scalable down to 16×16 favicon / app-icon / X avatar at small size. Must read at tiny scale and at hero scale. No text.

- **Variant 1 — Archway-A.** The letter A as a sheltering archway, with the crossbar evocative of a doorway lintel and the counterform suggesting a small interior. Warm single color on neutral ground. Very small number of strokes.
- **Variant 2 — Terracotta-roof.** An abstracted overlapping-tile roofline forming a simple geometric mark that reads as *shelter-over-something* without naming the thing sheltered. Stylized flat vector.

### 5.2 Wordmarks (2)

Typography only, no accompanying symbol. For contexts where the mark is too abstract or too small to carry (footer, receipt, documentation).

- **Variant 3 — Humanist wordmark.** The word *Abrigo* in a contemporary humanist sans-serif with one subtle custom cue — for example, the terminal on the final *o* closing to enclose the baseline, implying shelter through kerning rather than illustration. Single color.
- **Variant 4 — Editorial display wordmark.** *Abrigo* set in a display-scale contemporary sans (think between Graphik and Söhne rather than Didot) at large size, intended for deck covers and landing heroes where the word itself carries the brand. No illustration.

### 5.3 Combinations (2)

Symbol + word. For landing hero, deck cover, letterhead, business card.

- **Variant 5 — Archway-A + Humanist wordmark, stacked.** Variant 1's mark above Variant 3's wordmark. Vertical lockup.
- **Variant 6 — Terracotta-roof + Humanist wordmark, inline.** Variant 2's mark to the left of Variant 3's wordmark. Horizontal lockup.

### 5.4 Scenes (2)

Brand imagery, not logos. For landing-hero background and deck-cover imagery where a photographic or illustrated scene carries the mood and the wordmark sits on top.

- **Variant 7 — Courtyard-light scene.** Interior courtyard at morning, warm light falling across a terracotta-tiled floor, carved wooden door ajar showing a sheltered interior. No people. Editorial photography feel (not illustration). Abrigo wordmark overlaid in a corner.
- **Variant 8 — Terracotta-roof morning scene.** Exterior rooftop view at dawn, overlapping clay tiles receding toward soft mountain light (or urban horizon depending on iteration). Abrigo wordmark overlaid. Warm palette; no people; no architectural label.

---

## 6. Per-Variant Prompt Schema

Every variant in the library is a self-contained markdown block with exactly these sections, in order:

1. **Variant name and role** — e.g., "Variant 1 — Archway-A (symbol-only mark, favicon-scale)."
2. **What it emphasizes** — one or two sentences on which positioning lever the variant pulls (shelter metaphor, warmth, scalability, authoritative quiet, etc.).
3. **Usage** — explicit list of surfaces this variant is for (app icon, X avatar, landing hero, deck cover, letterhead, business card, email signature, etc.).
4. **Full Midjourney prompt** — the actual prompt text with parameters. Prose-style as Midjourney accepts, with explicit parameters (`--ar`, `--v 6`, `--style raw`, `--stylize`).
5. **Negative guidance** — the bans from §4.2 stated concretely for this variant, plus any variant-specific bans.
6. **Iteration notes** — variations to try if the first generation misses (e.g., "if the archway reads too baroque, tighten to geometric-only monoline; if the warm color reads as folk-craft, shift palette toward single-color navy + cream").

No other sections. No freeform commentary outside these six fields per variant.

---

## 7. File Layout

All library content lives in the gitignored Abrigo branding workspace.

- `contracts/.branding/artifacts/logo-prompts/drafts/v{N}.md` — the 8-variant library during review.
- `contracts/.branding/artifacts/logo-prompts/drafts/v{N}-facts-snapshot.yml` — facts snapshot (minimal; most variants cite no facts but the library top matter references `brand_name: Abrigo` and `pilot_market: Colombia` for cultural-fit context).
- `contracts/.branding/artifacts/logo-prompts/drafts/v{N}-source-manifest.md` — empty or near-empty; logo prompts do not cite painkiller evidence. Present for lifecycle uniformity.
- `contracts/.branding/artifacts/logo-prompts/reviews/v{N}-<seat>.md` — per-reviewer verdicts.
- `contracts/.branding/artifacts/logo-prompts.md` — graduated final library after three PASS verdicts at the same revision.
- `contracts/.branding/artifacts/logo-prompts-source-manifest.md` — graduated source manifest (stub).
- Optional, post-graduation: `contracts/.branding/artifacts/logo-prompts/samples/` — where the founder drops the best image generated per variant, with the Midjourney seed / URL noted alongside. Purely reference.

---

## 8. Authorship and Review

### 8.1 Authorship

The **Image Prompt Engineer** specialist from the agent catalog authors every revision of the library. The brand agent is NOT the author — image prompts are a different craft than copy, and the Image Prompt Engineer's charter matches this work directly. The Image Prompt Engineer reads the relevant Abrigo positioning memory files, the visual vocabulary in §4, and the library structure in §5, and produces the eight variants per the §6 schema.

### 8.2 Review triad

Every revision is reviewed by three seats in parallel. The triad is different from the copy-artifact triad because image prompts have different failure modes.

| Seat | Charter for logo artifacts |
|---|---|
| **Image Prompt Engineer (self, re-invoked)** | Technical prompt quality — Midjourney syntax, parameter calibration, negative-prompt discipline, prompt length, cliché avoidance. Self-review is acceptable here because it is a technical craft check, not a content check. |
| **Brand Guardian** | Abrigo brand contract — vocabulary adherence, the §4.2 ban list, no colonial labeling, no crypto cliché, no stereotype imagery, visual vocabulary alignment with the warm-but-disciplined hybrid. |
| **Cultural Intelligence Strategist** | Regional-reading check — does every variant pass the three cultural-fit discipline reads in §4.3; is any shelter element inadvertently stereotyping; do the vocabulary choices translate across the pilot market and the mission scope. |

The **Claim Auditor is not seated** for logo-prompt artifacts because image prompts carry no painkiller claims. Evidence grounding does not apply to visual-vocabulary choices.

### 8.3 Lifecycle

Identical to the copy-artifact lifecycle in spec `2026-04-15-abrigo-branding-agent-design.md` §7.4: drafts named `v{N}.md`, review verdicts at `reviews/v{N}-<seat>.md`, graduation requires three PASS verdicts all at the same revision `N`, hard cap at 5 revisions.

Founder override protocol and contradiction-surfacing rule also carry over unchanged from the parent spec.

---

## 9. Open Questions and Risks

### 9.1 Image Prompt Engineer charter fit

The Image Prompt Engineer agent's catalog description names photography and general AI image generation. Its actual frontmatter charter must be verified to match this spec's §8.1 authorship expectation. If the agent is photography-first and brand-logo-work requires substantial prompt-discipline redirection, author a dispatch-time augmentation template similar to the Claim Auditor pattern rather than amending the agent itself.

### 9.2 Cultural Intelligence Strategist double-seat

CIS sits in the Abrigo copy-artifact triad (spec `2026-04-15-abrigo-branding-agent-design.md` §7.1 tagline / positioning seat) AND in the logo triad here. The two dispatches serve different purposes (copy vs. visual vocabulary), but if the founder sees CIS return contradictory findings across copy and logo revisions, that is a drift signal — the brand's visual and verbal identities are out of alignment. Monitor.

### 9.3 Self-review exception

Allowing the Image Prompt Engineer to self-review is a departure from the no-self-review rule in spec `2026-04-15-abrigo-branding-agent-design.md` §6.3. The exception is narrow: the Engineer reviews only its own prompts for technical craft, not for brand or cultural content. Those are checked by the other two seats. If self-review drift shows up in practice (Engineer rubber-stamping its own work), replace with a second Image Prompt Engineer dispatch or add a Senior Developer review for prompt technical quality.

### 9.4 Midjourney version drift

Prompts are pinned to `--v 6` today. When Midjourney releases a new version with different prompt-adherence behavior, every variant may need tuning. The iteration-notes field per variant gives the founder a starting point for manual tuning; a full library refresh may be required after major MJ version jumps.

### 9.5 Color palette is deferred

The vocabulary in §4.1 names warm ochre + cream and deep teal + cream as example palettes, but the spec does not commit to a specific hex set. That is intentional — color choice is a downstream design decision after the founder picks which variant family to run with. A later spec (visual identity standards) will pick the exact palette.

---

## 10. Next Steps

Following approval of this spec:

1. **Three-way spec review.** Per `feedback_three_way_review.md`: Code Reviewer + Reality Checker + Technical Writer on this spec. Given tight credit budget, the founder may waive this review for a low-stakes library spec and proceed directly to implementation; that decision is the founder's.
2. **Implementation plan.** Invoke the writing-plans skill. Plan covers: creating the `logo-prompts/` directory tree, dispatching Image Prompt Engineer to author v1, dispatching the review triad, iterating to graduation.
3. **Verify Image Prompt Engineer charter.** Before first dispatch, read the agent's frontmatter and prompt body to confirm §9.1's fit concern.
4. **Author v1 library** via Image Prompt Engineer.
5. **Review triad on v1**; iterate to PASS.
6. **Graduate to `logo-prompts.md`**; founder generates images against the prompts.
7. **Optional samples capture.** Founder drops best images into `logo-prompts/samples/` with seed / URL for reference.
8. **Follow-on specs (out of scope for v1):** DALL-E and Stable Diffusion ports, color palette standards, typography specimens, full visual identity guide.

---

## 11. Sources of Truth

- **Brand name and parent-company context:** memory file `project_ran_brand_name.md` (d²π Labs parent; Abrigo retail sub-brand).
- **Positioning principles:** memory file `project_ran_positioning_principles.md`.
- **Two-tier field rule:** memory file `project_abrigo_two_tier_field_rule.md` (image prompts are Tier 1 story surface — vocabulary bans apply).
- **Copy-artifact lifecycle reference:** `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` (Rev 3) §7.4 lifecycle, §7.2.1 charter tiebreakers, §14 permissions, §15 reviewer agent inventory.
- **Existing d²π Labs logo prompts (reference only, not reused):** `contracts/.scratch/dsquared-pi-logo-prompt.md`.
- **Graduated Abrigo tagline artifact (sibling context):** `contracts/.branding/artifacts/taglines.md`.
