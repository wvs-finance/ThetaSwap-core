# Gate B1 — Phase 1 Implementation Review (3-way) — Path B Stage-2

**Convened:** 2026-05-04
**Scope:** Validate Phase 1 outputs (allowlist + TDD scaffold + audit + bugfix + Parquet emission + swap_flow inventory) before Phase 2 dispatch
**Convention:** `feedback_implementation_review_agents` — Code Reviewer + Reality Checker + Senior Developer (fresh) in parallel
**Spec sha pin:** `fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95` (v1.4)
**Plan sha pin:** `7e2f43c211a314475c3fc2ef5890c268c7216efa55b0b7a9d2c8e5d8d95bca6b` (v1.1)

## §1. Phase 1 commit chain reviewed

| Commit | Description |
|--------|-------------|
| `2483f08d3` | plan-Task 1.1 — 13-contract allowlist + DATA_PROVENANCE.md |
| `6d9c8dfc6` | TDD scaffold (5 RED tests at test_v0_audit.py + v0_audit.py stub) |
| `898d44910` | plan-Task 1.2 v1 (BUGGY) — false-positive HALTs from max_chunks=6 cap |
| `3116f818f` | BUGFIX amendment — re-audit unhid 51K COPm + 8.5M USDm events; verdict 4 PASS / 1 marg / 8 HALT |
| `821f6f1ca` | plan-Task 1.3 — 3 Parquet artifacts per spec §4.0 BLOCK-B1 schema; pytest 5/5 GREEN |
| `0dc05c5c9` | plan-Task 1.3.b — mento_swap_flow_inventory.parquet per spec §4.0 Artifact 4; BiPool USDm/COPm exchange-id pinned `0x1c9378bd...` |

## §2. Verdict integration

| Reviewer | Verdict | NITs/FLAGs | Recommendation |
|----------|---------|-------------|----------------|
| **Code Reviewer** | **PASS_WITH_NITS** | 6 NITs | PROCEED_TO_PHASE_2 |
| **Reality Checker** | **ACCEPT_WITH_FLAGS** | 5 FLAGs | PROCEED_TO_PHASE_2 |
| **Senior Developer (fresh)** | **ACCEPT_WITH_REMEDIATION** | 3 NITs + mandatory user-adjudicated HALT before Task 2.1 | PROCEED_TO_PHASE_2 |

**Final Gate B1 verdict: PASS — Phase 2 dispatch UNBLOCKED, conditional on substrate-pivot user adjudication per anti-fishing discipline.**

All three reviewers concur on PROCEED_TO_PHASE_2; zero BLOCKs; convergent confirmation that:
- Bugfix is evidence-grounded (Forno corroboration of COPm 0→181→234 events at window start/middle/end), not threshold-tuned (formula-derived `max(30, ceil(window/chunk_size)+2)`)
- Audit findings structurally honest (USDm 8.5M events ≈ flagship token; COPm 51,802 events ≈ 2× annual holder turnover plausible; 8 remaining HALTs are STRUCTURAL not script bugs)
- CORRECTIONS-γ structural-exposure framing preserved verbatim (no WTP / behavioral-demand language)
- Anti-fishing posture preserved (q_t pre-pinned in spec §3.B; HALTs surfaced via typed exceptions; bugfix discovery process matches `feedback_pathological_halt_anti_fishing_checkpoint`)
- Free-tier compliance verified (peak SQD 3.75 req/s under 5/s cap; 10 Alchemy CU total over Phase 1)
- 5/5 pytest GREEN; spec/plan sha pins embedded in driver scripts + Parquet metadata

## §3. Mandatory HALT before Phase 2 Task 2.1 — substrate-pivot user adjudication

Per **SD verdict**: "Phase 2 dispatch brief MUST surface the (a)/(b)/(c) substrate-pivot decision to user as a HALT-and-flag before Task 2.1 (per `feedback_pathological_halt_anti_fishing_checkpoint` — auto-pivot from spec-frontmatter PRIMARY to §6-Pivot-(a) is anti-fishing-banned without explicit user adjudication + CORRECTIONS-block)."

### §3.1 Why the HALT fires

Spec v1.4 §3 v1 a_l substrate pre-pins:
- **PRIMARY**: Mento V3 FPMM USDm/cUSD `0x462fe04b...`
- **SECONDARY**: Mento V2 BiPool USDm/COPm exchange (id `0x1c9378bd...` discovered Task 1.3.b)

Phase 1 audit findings (cb94f0588d... + 0dc05c5c9):
- PRIMARY: **0 events** over 136 weeks (genuinely dormant; structural truth not script bug)
- SECONDARY: **302 swaps** total — **PASSES** spec §6 100-swap-events floor — but **only $75K non_lp_user notional + $43K mev_arb cumulative** over 27 months

Plus Reality Checker FLAG-F3 (load-bearing): **lp_mint_burn = 0 across ALL substrates**. Mento V2 BiPool has NO user-LP surface (protocol-governed reserves only). r_(a_l) cannot be reconstructed as user-LP fee yield in the Uniswap-style sense.

This creates a real Phase 2 v1 r_(a_l) reconstruction substrate gap.

### §3.2 Three options for orchestrator/user adjudication

**Option (a) — Mento V2 BiPool aggregate fee yield (spec §6 Pivot-(a) authorized)**
- Reconstruct r_(a_l) as protocol-side accrued yield: BiPool spread + protocol-fee structure rather than user-LP fee tier
- Substrate: 302 BiPool USDm/COPm swaps + 114K BiPoolManager Mint/Burn events (protocol expansion/contraction)
- Pre-authorized by spec §6 "fall back to the secondary v1 substrate (Mento V2 BiPool USDm/COPm exchange) as the primary a_l-side substrate with explicit CORRECTIONS-block"
- Preserves Mento-corridor integrity for Phase 3 bound-check coupling
- CON: thin substrate ($75K direct non_lp_user notional); r_(a_l) precision will be limited by sample size

**Option (b) — Wait/defer until V3 USDm/COPm has activity**
- No spec change; await organic Mento V3 deployment
- CON: indefinite — no V3 USDm/COPm activity has materialized in 136 audit weeks (Aug 2023 → Feb 2026); could remain dormant indefinitely

**Option (c) — Pivot to Aave V3 Celo USDm pool (lending yield not LP fee yield)**
- Aave V3 Celo USDm depositors earn lending yield from corridor-borrowers (decoupled from FX vol direction; spec §1 LVR-acknowledgment-defensible per LP=short-variance result and user's earlier confirmation)
- Substrate: Aave V3 Celo Pool `0x3e59a31363e2ad014dcbc521c4a0d5757d9f3402` (per allowlist + SYNTHESIS.md §4.1)
- CON: decouples a_l from Mento corridor; Phase 3 bound-check coupling weakens (synthetic Δ^(a_s) ceiling no longer bounds against same-pool empirical r_(a_l))
- CON: spec §6 does NOT pre-authorize this pivot — would require explicit spec v1.4.1 micro-edit + 2-wave verify before Phase 2 dispatch

## §4. NITs to fix before final commit (cosmetic; non-blocking)

### §4.1 From CR
- **NIT-3** (LOAD-BEARING for v1+): event_inventory.parquet has FABRICATED topic0 placeholders (TOPIC0_UNIV3_POOL_CREATED off by 1 byte; Mento + Panoptic topics fake). Source script docstring claims "All values verified against on-chain event topics" — that claim is FALSE. Safe for v0 (column not consumed downstream) but Phase 2 must replace via real keccak256 before any join on topic0. **Phase 2 dispatch brief should include topic0 cleanup as a Task 2.0 sub-deliverable.**
- **NIT-4 + NIT-5**: DATA_PROVENANCE.md Entry 6 duplicated (lines 248 + 278; pre-bugfix + post-bugfix); stale "max 6 chunks" narration. **Cleanup pass before Phase 2 dispatch.**
- NIT-1: hard-coded WORKTREE absolute paths (intentional per cross-worktree-write incident lesson)
- NIT-2: venue_id-naming collision risk in v1+ (low priority)
- NIT-6: v0_audit.py stub now dead code (driver scripts implement directly)

### §4.2 From RC
- **F1**: Headline aggregates ($305M/$471M/$0) are SUBSTRATE-AGGREGATE not BiPool-USDm/COPm-specific. Phase 2 dispatch brief must clarify that for Pair D COP corridor, the load-bearing direct substrate is BiPool 302 swaps / $75K non_lp_user, NOT the broker-routed $305M aggregate.
- **F3**: lp_mint_burn=0 substrate truth — informs r_al estimator design (BiPool Mint/Burn events for protocol-side expansion/contraction, not user-LP fee accrual).
- **F4**: Mento V3 USDm/cUSD pool 0x462fe04b... not independently verified against Mento V3 deployment manifest. **Phase 2 dispatch brief should include 1-call eth_call token0/token1 sanity check before relying on the genuine-zero finding.**
- F2: Broker non_lp_user sparse (14 of 136 weeks nonzero); Phase 3 q_t generator must accommodate.
- F5: $471M mev_arb is LOWER bound (Eigenphi paywall fallback to Layer-2-only atomic-arb detection).

### §4.3 From SD
- NIT-1: findings.md (plan Task 1.5 deliverable) NOT yet emitted — this gate_b1_review.md serves as Task 1.5 close artifact.
- NIT-2: same as CR's NIT-4 (DATA_PROVENANCE Entry 6 duplicated).
- NIT-3: audit_summary "Mento V2 USDm" venue labeled `mento_fpmm` venue_kind but is actually the cUSD/USDm token contract — venue_kind enum mis-applied. Cosmetic; doesn't affect Phase 2 substrate routing (which uses BiPool exchange-id pinning).

## §5. Action items (post-Gate-B1-PASS)

1. **HALT for user**: surface §3.2 (a)/(b)/(c) decision before Phase 2 Task 2.1 dispatch
2. **Cosmetic cleanup pass**: fix NITs 3, 4, 5 (CR) + NIT-3 (SD) — single small commit before Phase 2
3. **Phase 2 dispatch brief preconditions**:
   - Topic0 keccak256 cleanup (replace fabricated placeholders)
   - V3 pool address verification (1-call eth_call token0/token1)
   - Substrate-pivot CORRECTIONS-block per chosen Option (a/b/c)
   - Sparse-week handling for q_t generator (per RC F2)
4. **Open PR for Phase 1**: after cleanup + substrate decision lands
5. **Then Phase 2 dispatch** under chosen substrate

## §6. Provenance

- Authored by orchestrator 2026-05-04 integrating CR + RC + SD reviewer outputs
- All 3 reviewer outputs are tool-call results in current session transcript; can be archived to `gate_b1_cr_review.md`, `gate_b1_rc_review.md`, `gate_b1_sd_review.md` if desired
- Spec + plan sha pins recorded at top
- This file is committable as the Phase 1 Task 1.5 close artifact

End of gate_b1_review.md.
