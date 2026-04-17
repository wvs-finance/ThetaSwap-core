# Abrigo Logo Prompt Library v1 Retrospective

**Date:** 2026-04-15
**Graduated at:** revision v2
**Total revisions to graduation:** 2 (v1 → v2)

## Lifecycle metrics

- v1 dispatched: Image Prompt Engineer with charter redirect for flat-vector work.
- v1 reviews: Brand Guardian BLOCK (F1 missing masterpiece/8k in V3–V6, F2 parent-brand leak risk), IPE self FLAG (5 craft findings), CIS FLAG (V7 carved-wooden-door colonial drift + V8 coverage gap).
- v2 dispatched: Image Prompt Engineer absorbing all 8 findings.
- v2 reviews: all three PASS. Graduation.

## What worked

1. **Charter-redirect discipline held under review pressure.** The Image Prompt Engineer's native photography posture did not leak into the flat-vector variants. The explicit suppression vocabulary in every variant's negative-guidance section (no photorealistic / masterpiece / 8k / ultra-detailed / cinematic lighting / studio lighting / golden hour / bokeh / f/1.8) was the load-bearing piece. v1 missed two tokens (masterpiece, 8k) on four variants; v2 closed that.
2. **Concrete shelter vocabulary prevented stereotype drift.** By specifying "terracotta clay tile," "woven textile," "stitched felt" rather than letting Midjourney infer "Latin American architecture," the prompts bypassed the pan-Latino stereotype shortcuts the ban list would have to catch otherwise.
3. **Woven-textile emerged as a clean fallback vocabulary.** CIS surfaced woven-textile as a mission-scope-translation alternative during v1 review; Brand Guardian confirmed as PASS when it appeared in v2. The vocabulary pulls its weight across LatAm and extends to MENA / South Asia contexts.
4. **Scene-variant separation worked.** V7 (interior-domestic courtyard) and V8 (exterior-landscape roofline) now cover distinct shelter contexts without doubling down on any single cultural frame.

## What broke or almost broke

1. **"Carved wooden door" colonial drift.** Midjourney's default for "courtyard + wooden door + terracotta" pulls heavily toward Spanish-colonial and baroque. The v1 positive steers (editorial register, Cereal / Kinfolk aesthetic) were not strong enough to overcome the default pull. CIS caught it. v2 replaces the focal element with less colonially-coded shelter imagery.
2. **Parent-brand leak risk.** The d²π Labs mention in the Library Context section was never intended for prompt body use but could have been copy-pasted accidentally. v2 moves the reference to a non-copy-pasteable location.
3. **Ban-list arithmetic drift.** v1 enumerated photography-drift tokens for some variants but not others. Consistent enforcement across all six logo-type variants required manual verification in v2.

## Vocabulary additions worth baking into spec §4 for next image-adjacent artifact

- **Ban `masterpiece` and `8k` explicitly** in the photography-drift ban floor for any flat-vector logo artifact (not just rely on `photorealistic` to carry it).
- **Woven-textile vocabulary** is added to the mission-scope-translation toolkit. It travels better than terracotta roof alone.
- **Library-Context sections must be marked non-copy-pasteable** in any artifact that mixes contextual prose with prompt bodies. A `<!-- DO NOT COPY INTO PROMPT BODY -->` fence is adequate.

## Charter drift observed

- **Image Prompt Engineer charter** held under dispatch-time redirect. The photography charter did not leak into flat-vector work on v2. Self-review was adequate as the technical-craft seat; no false PASSes observed.
- **Cultural Intelligence Strategist charter** caught the one cultural-drift issue (V7) that Brand Guardian would not have caught on its own. §7.2.1 tiebreaker held — CIS flagged only what Brand Guardian's charter could not see.
- **Brand Guardian charter** held tightly on the positioning-and-bans dimension. The two v1 findings (F1, F2) were exactly the type of brand-contract-surface issues this seat is supposed to catch.

## Process notes for next image-adjacent artifact

- Two revision rounds felt tight but adequate. Five would be too many; one would have shipped with bugs. Keep the hard cap at 5 but aim for 2–3.
- The diff-rationale file (v2-diff-rationale.md) made the second-round review faster because each reviewer could verify "your v1 finding X is closed" directly rather than re-scanning the whole artifact.
- Self-review by the same agent that authored (IPE) is acceptable for narrow technical-craft scope but should never be the only check. The two other seats (Brand Guardian, CIS) are the real quality gates.

## Graduated artifact locations

- Final library: `contracts/.branding/artifacts/logo-prompts.md`
- Source manifest: `contracts/.branding/artifacts/logo-prompts-source-manifest.md`
- Draft history (provenance): `contracts/.branding/artifacts/logo-prompts/drafts/`
- Review history: `contracts/.branding/artifacts/logo-prompts/reviews/`
