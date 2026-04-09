# Spec Completeness Review -- Rev 6
Reviewer: Mama Bear | Date: 2026-04-09 | Verdict: FLAG

## Findings

**F1 (BLOCK-level diagram inconsistency):** Section 3 diagram still says "Rev 5" and contains two stale artifact from the old architecture:
- `Accepts: asset0` label inside the V_B vault box -- contradicts Sections 2.1 and 4.2 which correctly say V_B accepts asset1.
- `Pool pair: asset0 / V_B_shares` in the PanopticPool box -- must read `V_A_shares / V_B_shares` (the Rev 5/6 model).
These are the two old-architecture artifacts explicitly flagged in the review brief.

**F2 (stale cross-refs in Section 10):** QA log references "Section 2.6" (hybrid clone-proxy) and "Section 2.7" (SFPM adapter). After renumbering these are now 2.8 and 2.9 respectively. Two broken cross-refs.

**F3 (diagram noise):** The Section 3 diagram contains raw draft inline comments (`// note: V_B vault receives asset_1 AND the shares are also measured...`, `// note: There is the V_A...`, `// note: KEY: THE transformations...`). These are not readable architecture prose and leak implementation uncertainty into a finished spec section.

**F4 (Section 4 vs four-layer model):** Section 4 component descriptions do not reference the Layer 1-4 framing introduced in Section 2.5. A new reader jumping directly to Section 4 will not understand which layer each component occupies. Suggest one-line layer callouts per component (e.g., "Layer 1 (Oracle)" for the Accumulator Source).

## Passing Checks

- Sections 2.5 and 2.5a are clear and well-structured for a new reader.
- All three new Section 9 research references are present and paths match scratch directory.
- Sections 2.2, 4.3, 4.4 consistently describe ct0/ct1 roles under the new V_A/V_B model.
- No Solidity or function signatures appear in architectural sections 2-8.
- Sections 6, 7, 8 are internally consistent with the four-layer model.
- Section 11 existing code inventory is unchanged and accurate.

## Required Before Next QA Round

1. Fix diagram V_B label: `Accepts: asset0` -> `Accepts: asset1`.
2. Fix diagram PanopticPool pool-pair line: `asset0 / V_B_shares` -> `V_A_shares / V_B_shares`.
3. Update Section 3 header from "Rev 5" to "Rev 6".
4. Update Section 10 cross-refs: 2.6 -> 2.8, 2.7 -> 2.9.
5. Remove or move draft inline comments from Section 3 diagram.
6. Optional (clarity): add layer callouts to Section 4 component headers.
