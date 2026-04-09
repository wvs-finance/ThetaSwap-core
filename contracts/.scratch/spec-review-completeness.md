# Spec Review: 2026-04-09-angstrom-panoptic-vault-architecture-design.md

Reviewer: Mama Bear (automated spec review)
Date: 2026-04-09
Spec status at review: Draft

---

## 1. Code Leakage

**Overall verdict: Borderline — several instances warrant deliberate decisions.**

The spec is mostly clean prose. There is no Solidity source code, no ABI fragments, and no function bodies. However, there are function-call expressions embedded in prose that blur the line between "naming a concept" and "prescribing an interface."

### Instances found

| Line(s) | Content | Assessment |
|---|---|---|
| 41 | `` `deposit()` `` and `` `withdraw()` `` | Borderline. These are standard ERC-4626 user-facing verbs. Acceptable if framed as behavior names, not as interface requirements. |
| 53 | `` `totalAssets = deposits + k * accumulator_delta` `` | This is a pseudo-formula, not real Solidity. Acceptable as math notation but should be written in proper formula syntax (e.g., `totalAssets(t) = deposits + k * (g(t) - g(t0))`) to avoid confusion with a code expression. |
| 68 | `` `AccrualManagerMod.viewAccruedRatio()` `` | This is a concrete function signature from the existing codebase, mentioned as a pointer to existing work. Acceptable in Section 9 (code inventory) but not in Section 2 (Design Decisions). Move this reference to Section 9 or rewrite it as "the accrued-ratio view function in AccrualManagerMod." |
| 107–108 (ASCII diagram) | `collateralToken0() --> ...` and `collateralToken1() --> ...` | These are Panoptic function signatures appearing inside an architecture diagram. The diagram is illustrating the wiring topology — the function names are incidental labels. Low risk, but they could be replaced with "CT0 slot" / "CT1 slot" to stay fully code-agnostic. |
| 178 | `` `AccrualManagerMod.viewAccruedRatio()` `` | Same issue as line 68. Concrete function name in a descriptive section. Replace with prose: "the accrued-ratio computation in AccrualManagerMod." |
| 241 | `` `checkCollateral` `` | Panoptic internal function name in an invariant statement. Should be rephrased as "the collateral-check routine" or "Panoptic's margin check." |
| Section 2.7 / line 68 | `` `extsload` `` | Low-level EVM opcode / Foundry cheatcode name. This is an implementation detail (the mechanism the adapter uses to read storage). An architecture spec should say "reads Angstrom's storage directly" rather than naming the opcode. The same word appears again in the risks table (line 260) which is fine there as a named risk. |

### Action required

- Replace bare function-call expressions (`viewAccruedRatio()`, `checkCollateral`, `collateralToken0()`, `collateralToken1()`) in Sections 2, 4, and 6 with descriptive names.
- Rewrite the pseudo-formula in Section 2.5 in math notation rather than code notation to avoid it being read as an interface contract.
- Decide whether `deposit()` / `withdraw()` on line 41 should stay (they are standard ERC-4626 user verbs) or be replaced with "the standard vault deposit and withdrawal operations."
- `extsload` in Section 2.7 prose should be replaced; its appearance in the risks table is acceptable as a named risk label.

---

## 2. Completeness

**Overall verdict: Good coverage for Phases 0–2. Phases 3–4 and several cross-cutting concerns are under-specified.**

### Well-specified areas

- Two-vault split rationale (Section 2.2) is thorough and self-justifying.
- V_B (ct1) component description (Section 4.2) is the strongest in the doc: observable is named, pricing logic is explained, preserved and changed behaviors are enumerated, invariants are stated.
- Invariants (Section 6) are precise and tied to their mathematical guarantees.
- Risk table (Section 7) is unusually good for a draft spec — each risk has a named consequence and a named mitigation.

### Under-specified areas

**Phase 3 (diamond ct0):**
Section 4.3 describes the diamond pattern as "dispatching based on the option's tick range" but does not explain:
- What determines which facet a given option position is routed to (tick range lookup? TokenId decode?)
- How a reader gets the correct `growthInside` for an arbitrary option leg when there are multiple facets
- Whether each facet stores its own accumulator snapshot or delegates to a shared store

This is actionable work and the spec gives an implementation team too little to act on for Phase 3.

**ct0 multi-period RAN / accumulator snapshot mechanism:**
Section 4.5 mentions "roll of single-period positions across epoch boundaries, achieved via accumulator snapshots (gas-efficient — no actual mint/burn per period)" but there is no component in Section 4 that owns this roll logic. Where does the snapshot live? Who triggers the roll? Is this inside ct0, inside PanopticPool, or in a new component?

**Conversion factor `k`:**
Sections 2.5, 4.2, and 4.3 all refer to a conversion factor `k` that maps Q128.128 accumulator units to asset-denomination token units. The spec does not explain:
- What `k` is numerically (is it the token's decimals? a Uniswap liquidity scalar? a fixed constant?)
- Whether `k` differs between ct0 and ct1
- Whether `k` is set at deploy time or computed dynamically

This is architecturally important because it determines whether the share price is correctly denominated and whether V_A/V_B is dimensionless (the ratio should be dimensionless for it to be a meaningful "concentration ratio").

**Virtual share anti-inflation initialization:**
Section 4.2 mentions "Virtual share anti-inflation initialization" is preserved, and Section 4.3 mentions "Virtual share initialization may need different parameters" without explaining what parameters, what range of values, or what criterion determines whether the default is adequate.

**IAccumulatorSource interface contract:**
Section 4.1 says the adapter provides "two read operations" but does not specify:
- The return types (Q128? scaled? raw?)
- Whether reads are checkpointed or spot values
- The failure mode when the Angstrom pool ID does not exist

---

## 3. Clarity for a New Reader

**Overall verdict: Readable for a DeFi-literate engineer. Requires prior Panoptic and Angstrom familiarity for Sections 4–6.**

### Terms that are defined inline (good)

- RAN, ratioInRange, V_A/V_B split, growthInside vs globalGrowth, ct0/ct1 naming convention — all explained on first use.

### Terms that are used without definition

- **"growth-outside accumulators"** (line 155): The spec says `growthInside` is "computed from the growth-outside accumulators" without explaining what growth-outside means or pointing to a reference. A reader unfamiliar with Uniswap V3 tick-math will not know what this means.

- **"PADE encoding" / "SSTORE2"**: These appear in the CLAUDE.md project context but not in the spec itself — no issue for the spec, but worth confirming the spec does not accidentally assume this context.

- **"Q128.128 format"** (multiple locations): Used as a technical fact without a footnote or definition. A one-line explanation ("a fixed-point representation where the value is stored as an integer scaled by 2^128") would make the spec self-contained.

- **"TokenId"** (Section 4.5): Used as if the reader knows Panoptic's TokenId encoding. A one-sentence gloss ("Panoptic's compact encoding of an option position: legs, strikes, widths, and risk partners packed into a single 256-bit value") is needed.

- **"Capponi's first-passage-time risk"** (risk table, last row): The academic citation is named but unexplained. A reader who has not read the Capponi paper will not understand what this risk is. Either expand the description ("the probability that a price process exits a finite range before a target time") or remove the eponym.

- **"UUPS or diamond"** (Section 2.6): Two different proxy patterns with different upgrade mechanics and different trust models are presented as interchangeable without criteria for choosing one. The spec should either pick one for Phase 1 or state the decision criterion.

- **"lpReward"** (Section 1): Used in backtick notation as if it is a field name from the very first line. A new reader does not know whether this is a variable, a concept, or a function. Expand to "the `lpReward` mechanism (Angstrom's Top-of-Block auction proceeds redistributed to LPs)."

### ASCII Diagram (Section 3)

The diagram is clear for the happy path. Two things are missing:
- The Factory (Section 4.4) is described as a core deployment component but does not appear in the diagram.
- The "IAccumulatorSource" boxes appear between Angstrom and the vaults, but the diagram does not show who instantiates them or whether they are standalone contracts or part of the vault logic.

---

## 4. Internal Cross-References

**Overall verdict: Mostly consistent. Three specific inconsistencies found.**

### Consistent references

- Section 5 (phased rollout) correctly maps each phase to the ct0 and ct1 states described in Sections 4.2 and 4.3. The "What It Proves" column aligns with the invariants in Section 6.
- Section 7 (risks) covers ct0 (range going out-of-range, node manipulation of growthInside), ct1 (pool generates zero rewards), the proxy layer (proxy upgrade bug), and the read layer (extsload stale data). All four major components from Section 4 have at least one risk entry.

### Inconsistencies

**Cross-reference 1: Factory omitted from risk table.**
Section 4.4 identifies the Factory as the component that ensures the shared PoolManager constraint is met. This is a deployment-time correctness requirement with real failure modes (factory deploys ct0/ct1 pointed at the wrong pool; PanopticPool immutable args baked in incorrectly). Section 7 has no risk entry for factory misconfiguration.

**Cross-reference 2: Phase 4 SFPM accumulator adapter is architecturally unanchored.**
Phase 4 in Section 5 introduces "SFPM accumulator adapter" as an optional Phase 4 feature. There is no corresponding component description in Section 4 and no invariant in Section 6 that addresses it. If Phase 4 is in scope, it needs at minimum a placeholder in Section 4 and a note in Section 6. If it is truly optional/exploratory, Section 5 should label it as "future research, not in scope for this design."

**Cross-reference 3: Section 2.7 rate provider pattern vs. Section 4.2 share pricing.**
Section 2.7 says V_B follows the Balancer IRateProvider pattern. Section 4.2 says V_B's `totalAssets` incorporates the accumulated reward delta. These are not contradictory, but they describe the same mechanism at different levels of abstraction without explicitly connecting them. A reader following Section 4.2 alone will not know a rate provider is involved. Add a cross-reference: "The rate provider described in Section 2.7 is the mechanism that delivers the accumulator delta to `totalAssets`."

---

## 5. Missing Sections

**Overall verdict: The following sections are absent and their absence will create blockers for an implementation team.**

### Missing: Deployment Strategy

The spec describes what gets deployed (two proxies + PanopticPool clone via custom factory) but does not cover:
- What network(s) this targets (mainnet, testnet, fork)
- What order contracts must be deployed in (are there circular dependencies between the proxies and PanopticPool?)
- What the initialization sequence is (who calls initialize on each proxy, in what order, with what arguments)
- Whether the deployment is gated behind a timelock or multisig from day one

### Missing: Testing Strategy

The spec references `PanopticPlayground.t.sol` as a proof that Angstrom + Panoptic share a PoolManager (Phase 0), and mentions "differential testing (fork test compares proxy vs reference)" in the risk mitigation for proxy upgrades. There is no testing strategy that covers:
- What invariant tests are required before Phase 1 goes live
- What the upgrade test harness looks like
- Whether fuzz testing is in scope for the share pricing functions
- What the Phase 2 acceptance criteria are before proceeding to Phase 3

### Missing: Success Criteria per Phase

Section 5 states "What It Proves" for each phase but does not state "What Must Be True Before Moving to the Next Phase." Without exit criteria, a team cannot determine when Phase 1 is done and Phase 2 can begin. This is distinct from what the phase proves — it is the verifiable gate.

### Missing: External Dependencies and Version Pins

Section 9 lists existing components but does not state:
- Which version of Panoptic's CollateralTracker is the baseline (the lib is dated `2025-12-panoptic`, but the spec should state this explicitly and note what happens if Panoptic releases a breaking update)
- Whether Solady ERC-4626 is a hard dependency or a recommended starting point
- Whether Balancer's IRateProvider is imported as a library or re-implemented from scratch

### Missing: Upgrade Governance

Section 2.6 states proxies use UUPS or diamond pattern and the implementation can evolve. Section 7 mentions a timelock as a mitigation. But there is no section describing:
- Who controls the upgrade key
- What the timelock delay is
- Whether upgrade capability is preserved indefinitely or burns after Phase 3
- Whether ct0 and ct1 upgrades are coupled or independent

This is an architecture decision (not implementation detail) and belongs in the spec.

### Missing: Handling of ct0 When No Range Is Configured (Phase 0 → 1 Transition)

In Phase 0, ct0 is vanilla CollateralTracker. In Phase 2, it reads `growthInside` for a "configured range." The spec does not describe:
- How the range is configured (constructor arg? admin call? factory param?)
- What happens if ct0 is queried before a range is configured
- Whether a range can be reconfigured after initial deployment (and what that means for existing depositors)

---

## Summary Table

| Dimension | Score | Top Issue |
|---|---|---|
| No code leakage | Borderline | 6 function-call expressions in prose sections; `extsload` as implementation detail in Section 2.7 |
| Completeness | Moderate gaps | Phase 3 diamond dispatch, conversion factor `k`, IAccumulatorSource return types |
| Clarity for new reader | Good with gaps | Undefined: growth-outside accumulators, Q128.128, TokenId, "Capponi first-passage-time" |
| Internal cross-references | Mostly consistent | Factory missing from risk table; Phase 4 architecturally unanchored; Sections 2.7 and 4.2 not cross-linked |
| Missing sections | Notable gaps | Deployment strategy, testing strategy, phase exit criteria, upgrade governance, ct0 range configuration lifecycle |
