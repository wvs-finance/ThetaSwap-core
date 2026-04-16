# Image Prompt Engineer Charter Check (Abrigo Logo Plan Task 0.1)

**Date:** 2026-04-15
**File inspected:** `/home/jmsbpp/.claude/agents/_archived/design/design-image-prompt-engineer.md`
**Frontmatter name:** `Image Prompt Engineer`

## Charter summary

The agent describes itself as an "Expert photography prompt engineer specializing in crafting detailed, evocative prompts for AI image generation. Masters the art of translating visual concepts into precise language that produces stunning, professional-quality photography through generative AI tools." Its stated identity is "Photography prompt engineering specialist for AI image generation."

The body of the prompt extends this coverage to: "portrait, landscape, product, architectural, fashion, and editorial photography genres," and includes "Brand alignment and style consistency across generated images" as one of its competencies. Critical rules section covers prompt structure (subject, environment, lighting, style, technical specs), concrete terminology over vague descriptors, negative prompts, aspect ratio / composition, and platform-specific optimization (Midjourney, DALL-E, Stable Diffusion, Flux).

## Fit for Abrigo logo prompt library

**Partial fit.** The agent is photography-first by charter, but:
- Midjourney prompt craft for logos and photography share ~80% of their mechanics: parameter calibration (`--ar`, `--v`, `--style`, `--stylize`), negative prompts, concrete vocabulary over vague descriptors, aspect-ratio discipline.
- The agent explicitly names "architectural" and "brand alignment" as within-scope domains.
- Logo mark work (flat vector, wordmark, combination mark, scene imagery) requires a craft posture the agent does not natively carry — the agent's defaults lean toward photorealistic composition, lighting setups, and camera perspective, which are the wrong defaults for a flat-vector logo mark.

**Conclusion:** dispatch-time augmentation is the right redirect, not agent-file modification. Per Abrigo branding-agent spec Rev 3 §15 option (c), we do not amend the underlying agent; we compose a per-invocation prompt that suspends photography defaults and activates flat-vector-logo-mark-work craft for marks and wordmarks, while leaving the photography charter active for the two architectural-scene variants where photography IS the target medium.

## Redirect content to embed in every Task 1.1 / Task 3.1 dispatch

When dispatching the Image Prompt Engineer for this library:

1. **Suspend photography-first defaults for logo-type variants.** Variants 1–6 (symbol marks, wordmarks, combinations) target flat vector / editorial graphic design output from Midjourney, not photography. Discourage photography vocabulary (bokeh, f-stop, golden hour, studio lighting) in these prompts. Prefer flat-vector vocabulary (monoline, single-weight stroke, geometric, grid construction, negative-space discipline, flat color).

2. **Photography charter stays active for scene variants.** Variants 7–8 (courtyard-light scene, terracotta-roof morning scene) ARE photography outputs intended as brand imagery with wordmark overlay. The agent's native craft applies — golden hour, editorial photography, wide shot, depth of field, warm palette grading.

3. **Negative-guidance section per variant must ban Midjourney's photography-drift defaults** for logo-type variants: no "photorealistic," no "masterpiece," no "8k ultra-detailed," no "cinematic lighting" tokens. These degrade logo-mark output.

4. **Per-variant prompt length.** Midjourney logo prompts are shorter than photography prompts — typically 30–80 words for marks, 50–120 for scenes. Avoid run-on prompts that dilute the mark's signal.

## Dispatchability check

"Image Prompt Engineer" appears in this session's active agent catalog despite the file living in `/home/jmsbpp/.claude/agents/_archived/design/`. Dispatch by `subagent_type: Image Prompt Engineer` is expected to work. If the dispatch fails at Task 1.1 with "agent not found," un-archive the file using the rename-on-move pattern established in the parent plan's Task 0.1 (move to `/home/jmsbpp/.claude/agents/image-prompt-engineer.md` and update README.md cross-links if needed).

## Decision gate

**Proceed to Task 0.2.** Charter is adequate with dispatch-time augmentation as planned. No spec revision needed.
