# FCI Derived Metric — Oracle Accumulation Fix

## Problem

The Solidity FCI oracle uses cumulative append-only accumulators (`accumulatedSum`, `thetaSum`, `removedPosCount`) that never decrease. This produces a monotonically increasing Δ⁺ signal with infinite memory — past high-concentration events permanently inflate the metric.

The backtest that validated P-squared payoff optimality uses daily-snapshot Δ⁺ computed fresh from each day's fee collections. Real data shows the signal going up and down freely:

```
2025-12-23: Δ⁺ = 0.175   (extreme JIT day)
2025-12-24: Δ⁺ = 0.001   (back to normal)
```

The cumulative oracle cannot reproduce this — after Dec 23's spike, Δ⁺ stays elevated indefinitely, only decreasing through slow dilution at O(1/√N).

This mismatch causes three downstream failures:
1. **Oracle over-reports** — Δ⁺ stays inflated after conditions improve
2. **Vault HWM locks in the over-report** — ratchets up, only decays with half-life
3. **Payoff caps out** — any above-strike reading saturates at Q96 (binary on/off)

Integration tests confirm: `longPayout = HEDGE_AMOUNT` (full cap) under JIT, `longPayout = 0` without. No proportionality.

## Approach

Implement a **strategy pattern** where the FCI oracle exposes multiple fee concentration metrics as parallel APIs. Each mechanism (cumulative, epoch-based, decay, sliding window) gets its own module with independent storage, receiving raw `(xSquaredQ128, blockLifetime)` from `afterRemoveLiquidity`. The oracle interface exposes all of them.

This serves two purposes:
1. **If Phase 2 produces a clear winner:** the vault uses it, but the others remain available for different derivative products with different risk profiles.
2. **If Phase 2 is ambiguous:** all viable candidates ship, and the market decides which metric best prices each instrument. Different derivatives (lookback options, trigger insurance, variance swaps) may prefer different accumulation models.

The existing cumulative `getDeltaPlus()` becomes one strategy among several — not special, just the first one implemented.

## Architecture

```
afterRemoveLiquidity:
    ... computes xSquaredQ128 = xk.square()
    ... computes blockLifetime from deregisterPosition()
    │
    ├── addStateTerm(hookData, poolId, blockLifetime, xSquaredQ128)
    │       → cumulative state (existing, untouched)
    │         └── getDeltaPlus() (unchanged)
    │
    ├── addEpochTerm(hookData, poolId, blockLifetime, xSquaredQ128)
    │       → epoch-based state (new module)
    │         └── getDeltaPlusEpoch()
    │
    ├── addDecayTerm(hookData, poolId, blockLifetime, xSquaredQ128)
    │       → decay-based state (new module)
    │         └── getDeltaPlusDecay()
    │
    └── addWindowTerm(hookData, poolId, blockLifetime, xSquaredQ128)
            → sliding-window state (new module)
              └── getDeltaPlusWindow()

poke() calls whichever metric the vault is configured to use
```

The fan-out happens **inside** `afterRemoveLiquidity`, after `xSquaredQ128` and `blockLifetime` have been computed. Each new module call receives the same arguments including `hookData` for the `isUniswapV3Reactive(hookData)` dispatch — new modules must follow the same V4-local vs reactive-V3 storage split pattern as `addStateTerm()`.

Each derived module:
- Lives at `src/fee-concentration-index/modules/FeeConcentration<Mechanism>Mod.sol` (main repo, alongside existing `FeeConcentrationIndexStorageMod.sol`)
- Has its own diamond storage slot (`keccak256("thetaswap.fci-<mechanism>")`)
- Receives raw `(hookData, poolId, xSquaredQ128, blockLifetime)` from the callback — fully decoupled from all other modules
- Never reads from other modules' storage
- Handles V4/V3-reactive dispatch via `hookData` flags

Only mechanisms that Phase 2 validates as viable get implemented. If a candidate performs poorly in the sweep, it's dropped — no dead code.

## Phases

### Phase 1 — Root Cause Confirmation (Python)

**Goal:** Quantify the divergence between cumulative and daily-snapshot Δ⁺, and its impact on payoff outcomes.

**Data:** Fresh Dune query for 50 positions alive on Dec 23, 2025 (the single outlier event). Per-position granularity: `token_id, mint_block, burn_block, fee_share_x_k, total_pool_fee, burn_timestamp`. The existing backtest's 600-position dataset serves as the reference anchor — the 50-position subset is filtered from it.

**Deliverables:**
- Dune query (new, optimized for 50-position window)
- Module: `research/backtest/oracle_comparison.py`
  - `PositionExit` frozen dataclass (token_id, burn_date, block_lifetime, fee_share_x_k)
  - `CumulativeOracleState` frozen dataclass (accumulated_sum, theta_sum, removed_pos_count)
  - `step_cumulative(state, exit) → CumulativeOracleState`
  - `daily_snapshot_delta_plus(exits_on_day) → float`
  - `build_dual_series(exits_sorted_by_burn) → DualDeltaPlusSeries`
- Notebook: `research/notebooks/oracle-accumulation-comparison.ipynb`
  - Cell 1: Plot both Δ⁺ series (daily-snapshot vs cumulative) on same axes
  - Cell 2: Feed both into existing `payoff.py` pipeline for the 50-position subset
  - Cell 3: Summary table — % better off, mean HV, payout distribution under each model
- Tests: `research/tests/backtest/test_oracle_comparison.py`

**Success criteria:** Cumulative Δ⁺ demonstrably diverges from daily-snapshot after Dec 23. Cumulative model produces degraded payoff metrics (lower % better off, binary payout distribution).

### Phase 2 — Mechanism Sweep (Python)

**Goal:** Identify which accumulation mechanism best reproduces daily-snapshot Δ⁺ behavior while being implementable on-chain.

**Candidates:**

| # | Model | Parameters to sweep | On-chain feasibility notes |
|---|-------|---------------------|---------------------------|
| 1 | Epoch reset | epoch length: 1d, 3d, 7d, 14d | Boundaries via `block.timestamp`; Phase 2 must evaluate timestamp granularity and MEV manipulation risk |
| 2 | Exponential decay | τ: 1d, 3d, 7d, 14d | Multiplication before each addTerm; gas-cheap (one extra SLOAD + mul) |
| 3 | Sliding window | last N exits: 10, 25, 50 | Ring buffer of N storage slots per pool; Phase 2 must flag if storage cost is prohibitive (N=50 ≈ 50 slots) |
| 4 | Daily snapshot | (none — the target baseline) | Reference model; may not be directly implementable on-chain (requires external epoch trigger or approximation) |

Open to adding candidates if none of the four produce acceptable results. Additional candidates require a brief spec addendum before implementation to avoid unbounded scope.

**Evaluation metrics** (all compared against daily-snapshot baseline):
- Correlation of Δ⁺ series
- % better off (from payoff pipeline)
- Mean hedge value (from payoff pipeline)
- Max divergence from daily-snapshot Δ⁺

**Deliverables:**
- Extend `oracle_comparison.py` with candidate step functions
- Notebook: new section in same notebook — grid of plots (candidate × parameter), ranking table
- Output: winning mechanism's analytical form + calibrated parameters

**Success criteria:**
- **Clear winner:** One candidate dominates on all metrics → vault defaults to it, others still ship as alternatives.
- **Ambiguous results:** Multiple candidates perform comparably → all viable ones ship as parallel oracle APIs. The market decides which metric best prices each derivative instrument.
- **All fail:** No candidate reproduces daily-snapshot behavior → spec this as a finding, revisit oracle architecture (may need event-level redesign rather than accumulation-level fix).

Minimum viability threshold per candidate: >0.8 correlation to daily-snapshot Δ⁺ AND non-negative mean HV in the payoff pipeline.

### Phase 3 — Solidity Multi-Metric Oracle (Strategy Pattern)

**Goal:** Implement all viable mechanisms from Phase 2 as parallel modules in the FCI oracle, each with its own API. The vault selects which metric to use. No existing tests broken.

**One module per viable mechanism.** If Phase 2 validates 3 of 4 candidates, 3 modules ship. If only 1 is viable, only 1 ships. The architecture supports all without dead code.

**Deliverables per viable mechanism:**

New files (per mechanism):
- `src/fee-concentration-index/modules/FeeConcentration<Mechanism>Mod.sol` — own diamond storage, own accumulators, own `deltaPlusFoo()` function
- `test/fee-concentration-index/unit/<Mechanism>Metric.t.sol` — unit tests
- `test/fee-concentration-index/fuzz/<Mechanism>Metric.fuzz.t.sol` — fuzz tests with Python differential

Modified files (once, regardless of how many mechanisms):
- `src/fee-concentration-index/FeeConcentrationIndex.sol` — after computing `xSquaredQ128` and `blockLifetime` in `afterRemoveLiquidity`, calls each module's `addTerm(hookData, poolId, blockLifetime, xSquaredQ128)`. Implements each `getDeltaPlus<Mechanism>()`.
- `src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol` — adds `getDeltaPlusEpoch()`, `getDeltaPlusDecay()`, `getDeltaPlusWindow()` (only for viable mechanisms)
- `src/fci-token-vault/modules/FciTokenVaultMod.sol` — `poke()` calls the best-performing metric (configurable via vault storage or hardcoded to Phase 2 winner)
- `research/data/scripts/fci_oracle.py` — adds each mechanism's computation for differential testing

**Gas budget:** Phase 3 includes gas benchmarks for `afterRemoveLiquidity` with all viable mechanisms active. Each module adds ~20K gas (cold SSTORE to independent diamond slot). If aggregate cost across all mechanisms exceeds acceptable bounds, consider lazy-evaluation (compute derived Δ⁺ at read time from cumulative state) or opt-in activation per pool.

Untouched:
- All existing FCI unit tests, fuzz tests, fork tests
- Kontrol proofs
- `getDeltaPlus()` (cumulative) — now one strategy among several
- `FeeConcentrationStateMod.sol` — no structural changes

**Validation:**
- Each mechanism's unit + fuzz tests pass independently
- Re-run `HedgedVsUnhedged.integration.t.sol` with the best-performing metric — should show proportional (non-binary) payoff behavior
- Full existing test suite passes unchanged

## Checkpoints

Every code modification (new file, modified file, or new module) must pass a checkpoint before proceeding:

- **Python changes:** `cd research && ../uhi8/bin/python -m pytest tests/ -v` — all existing + new tests pass
- **Solidity changes:** `forge build` compiles without errors, then `forge test` — full suite passes
- **After each Phase 3 module addition:** run `forge test --match-path "test/fee-concentration-index/**" -v` AND `forge test --match-path "test/fci-token-vault/**" -v` — zero regressions
- **Before any commit:** both Python and Solidity checkpoints pass

If a checkpoint fails, stop and fix before making further changes. Do not accumulate multiple modifications between checkpoints.

## Constraints

- **Python environment:** All Python code runs via the `uhi8/` virtual environment (`uhi8/bin/python`, `uhi8/bin/pytest`). No system Python.
- **Dune free tier:** ~2,489 credits remaining (community plan, 2,500/month). If credit-constrained, fall back to filtering the existing 600-position dataset to the Dec 23 window programmatically (loses per-position x_k² granularity but preserves daily aggregates).
- Existing backtest data (600 positions, daily aggregates) stays as reference anchor
- No modifications to existing FCI tests or cumulative oracle
- Python: frozen dataclasses, free pure functions, full typing (functional-python skill)
- Solidity: SCOP-compliant, no inheritance in production, no `library` keyword

## Dependencies

- Phase 2 depends on Phase 1 (same data, extended analysis)
- Phase 3 depends on Phase 2 (viable mechanisms determine which modules to implement)
- Phase 3 implements ALL viable mechanisms, not just the top one — ambiguous Phase 2 results are acceptable
- Existing backtest pipeline (`payoff.py`, `pnl.py`, `daily.py`) used as-is in Phases 1-2
- The vault defaults to the best-performing mechanism but the oracle exposes all viable ones for other derivative products
