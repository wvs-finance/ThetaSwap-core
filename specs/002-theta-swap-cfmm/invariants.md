# Invariants: ThetaSwap Fee Concentration Insurance CFMM

**Feature**: [spec.md](./spec.md) | **Data Model**: [data-model.md](./data-model.md)
**Count**: 41 invariants (31 CFMM model + 10 insurance-specific)

## CFMM Model Invariants (CFMM-01 through CFMM-31)

The 31 mandatory CFMM invariants are defined in [`specs/model/invariants.tex`](../model/invariants.tex). They cover:

- **Tier 1 (Structural)**: CFMM-01 through CFMM-05 — no-drain, output bound, supply biconditional
- **Tier 2 (Economic)**: CFMM-06 through CFMM-10 — gain formula, rate vs oracle, arbitrage (Bartoletti et al.)
- **Tier 3 (Rate Properties)**: CFMM-11 through CFMM-14 — monotonicity, homogeneity, additivity, reversibility
- **Tier 4 (State Machine)**: CFMM-15 through CFMM-19 — epsilon-slack, non-negativity, resource bounds, no rounding arbitrage, cross-tick
- **Tier 5 (Replication)**: CFMM-20 through CFMM-24 — payoff replication, hedge ratio, delta exposure
- **Tier 6 (Perpetual)**: CFMM-25 through CFMM-28 — funding rate convergence, mark-index alignment
- **Tier 7 (Fee Concentration)**: CFMM-29 through CFMM-31 — oracle integration, B_T consistency

All 31 invariants apply to this feature and will be verified via Kontrol proofs and fuzz tests per SC-008.

## Insurance-Specific Invariants (INS-001 through INS-010)

The following 10 invariants are specific to the insurance CFMM and extend the 31 model invariants above.

---

## INS-001: Premium Stream Conservation

| Field | Value |
|-------|-------|
| ID | INS-001 |
| Description | Every unit of premium deducted from a PLP's fee stream must be fully accounted for: total premium in equals underwriter earnings plus the protocol fee. No premium is lost or created. |
| Category | System-level |
| Formal Statement | `premium_in(t) == sum(underwriter_earnings_i(t)) + protocol_fee(t)` for every settlement period `t`. Equivalently, for any interval `[t0, t1]`: `integral(fee_stream, t0, t1) == sum(accrued_premiums_i) + protocol_fee_accrued`. |
| Rationale | Conservation is the foundational solvency guarantee. If premiums can disappear or be double-counted, underwriters cannot trust their yield and the market collapses. This invariant is the insurance analogue of the AMM constant-product conservation law. Derives from FR-008 and FR-011. |
| Test Strategy | Kontrol proof (`prove_premium_conservation`) verifying that each fee deduction event increments underwriter accumulators and protocol fee by exactly the deducted amount. Fuzz test over arbitrary fee stream sequences and underwriter liquidity distributions. |
| References | FR-008, FR-011, SC-003, SC-008 |

---

## INS-002: Auto-Close Threshold

| Field | Value |
|-------|-------|
| ID | INS-002 |
| Description | A PLP protection position closes if and only if its remaining margin is at or below `MIN_MARGIN`. No position may remain open below the threshold, and no position may be force-closed above it. |
| Category | Function-level |
| Formal Statement | `{margin[pos] <= MIN_MARGIN}` -> `afterFeeAccrual(pos)` -> `{pos.closed == true}`. Contrapositive: `{pos.closed == false}` -> `{margin[pos] > MIN_MARGIN}`. |
| Rationale | Auto-close is the primary mechanism preventing insolvent protection obligations. The biconditional formulation catches both false-positive closes (closing solvent positions) and false-negative closes (leaving insolvent positions open). Derives from FR-010. |
| Test Strategy | Unit test: boundary case `margin == MIN_MARGIN` triggers close; `margin == MIN_MARGIN + 1` does not. Kontrol proof (`prove_autoclose_iff_min_margin`) on the combined close condition. Fuzz test with random fee deduction sequences. |
| References | FR-010, SC-006, SC-009 |

---

## INS-003: Self-Sizing Hedge

| Field | Value |
|-------|-------|
| ID | INS-003 |
| Description | The insurance position size of a registered PLP scales proportionally with their current fee stream rate. A PLP earning twice the fees holds twice the protection notional, within one hook callback. |
| Category | System-level |
| Formal Statement | For any two PLPs `p1`, `p2` registered in the same pool: `protection_size(p1) / protection_size(p2) == fee_stream_rate(p1) / fee_stream_rate(p2)` at every hook callback boundary, provided both rates are nonzero. |
| Rationale | The self-sizing property ensures the hedge is always proportionate to the actual fee exposure. Over-hedging wastes premium; under-hedging leaves the PLP exposed. This also prevents a PLP from gaming protection by accumulating a large position before stopping their fee stream. Derives from FR-016 and SC-005. |
| Test Strategy | Fuzz test (`testFuzz_selfSizing_proportionality`) with two PLPs at varying fee stream ratios, asserting protection size ratio matches within one callback. Kontrol proof on the proportionality update in the fee deduction handler. |
| References | FR-008, FR-016, SC-005 |

---

## INS-004: Piecewise-Linear Error Bound

| Field | Value |
|-------|-------|
| ID | INS-004 |
| Description | Within any single tick interval, the piecewise-linear approximation of `y = x - ln(x) - 1` deviates from the exact curve by at most epsilon `e` in absolute terms. The coefficients stored per tick guarantee this bound for all `x` in `[x_lower, x_upper]`. |
| Category | Type-level |
| Formal Statement | For every tick `i` and every `x` in `[x_i, x_{i+1}]`: `|y_exact(x) - y_approx(x)| <= e` where `y_exact(x) = x - ln(x) - 1` and `y_approx(x) = slope_i * x + intercept_i`. The bound `e` satisfies `e < 10^-8 * y_exact(x)` per SC-001. |
| Rationale | The piecewise-linear design makes the trading function gas-efficient, but the approximation error must be bounded to ensure swap amounts are fair and arbitrage-resistant. Unbounded error would allow tick-level exploitation. Derives from FR-001 and SC-001. |
| Test Strategy | Unit test: for each precomputed tick, evaluate exact `y = x - ln(x) - 1` at 100 points within the tick range and assert relative error below `10^-8`. Fuzz test with random `x` values mapped to their tick and verify the bound. Kontrol proof (`prove_piecewise_error_bounded`) on coefficient derivation. |
| References | FR-001, FR-015, SC-001 |

---

## INS-005: Tick Crossing Liquidity

| Field | Value |
|-------|-------|
| ID | INS-005 |
| Description | When the active tick crosses a tick boundary during a swap or premium rebalancing, the active liquidity is updated by exactly the net liquidity delta stored at that tick. No other operation may change active liquidity at a tick crossing. |
| Category | Function-level |
| Formal Statement | `{L_active == L, crosses tick_c}` -> `crossTick(tick_c)` -> `{L_active == L + liquidityNet(tick_c)}` where `liquidityNet(tick_c)` is the signed net delta for underwriter positions entering or leaving at `tick_c`. |
| Rationale | Accurate liquidity tracking at tick crossings is essential for correct premium distribution. If active liquidity is mis-stated after a crossing, underwriters in the newly active range receive incorrect premium accruals and the CFMM price is wrong. Mirrors the Uniswap V3 tick crossing invariant but applied to the insurance CFMM. Derives from FR-012. |
| Test Strategy | Unit test: deposit underwriter positions on both sides of a tick, execute a swap that crosses the tick, assert `L_active` equals the sum of all in-range underwriter liquidity. Kontrol proof (`prove_tick_crossing_liquidity_update`). Fuzz test with multi-tick crossings. |
| References | FR-002, FR-012, SC-002 |

---

## INS-006: Oracle Consistency

| Field | Value |
|-------|-------|
| ID | INS-006 |
| Description | The index price `p_index` computed and cached by the insurance hook must always equal `B_T / (1 - B_T)` using the most recently read `B_T` from the FeeConcentrationIndex facet. Stale values and arithmetic deviations are not permitted. |
| Category | System-level |
| Formal Statement | After every hook callback that reads the oracle: `p_index_cached == B_T_read / (1 - B_T_read)` where `B_T_read` is the value returned by `IFeeConcentrationIndex.getIndex()` in the same transaction. For `B_T == 0`: `p_index == 0`. For `B_T >= 1`: reverts per edge case handling (FR-014). |
| Rationale | The index price is the anchor for the funding rate. Any divergence between `p_index` and the true `B_T / (1 - B_T)` corrupts the funding rate direction and magnitude, destabilizing mark-index convergence. The oracle call must be live — stale data is treated as failure per FR-014. Derives from FR-004, FR-005. |
| Test Strategy | Unit test: mock `IFeeConcentrationIndex.getIndex()` returning specific `B_T` values, assert derived `p_index` matches formula exactly including `B_T = 0` boundary. Kontrol proof (`prove_oracle_consistency`) on the index derivation arithmetic. Fuzz test with random `B_T` in `[0, 1)`. |
| References | FR-004, FR-005, FR-014, SC-009 |

---

## INS-007: Funding Rate Bounds

| Field | Value |
|-------|-------|
| ID | INS-007 |
| Description | The per-swap funding rate adjustment is bounded in absolute value by `fee_max - fee_base`. The total fee never exceeds `fee_max` and never falls below `fee_base`. |
| Category | Type-level |
| Formal Statement | For all market states: `fee_base <= fee(t) <= fee_max`. Equivalently, the adjustment term satisfies `|fee(t) - fee_base| <= fee_max - fee_base`, which gives: `fee(t) = fee_base + sign(p_mark - p_index) * min(alpha * |p_mark - p_index| / (p_index + 1), fee_max - fee_base)`. |
| Rationale | Fee bounds prevent the funding rate from becoming punitive during extreme price dislocations. Without the cap, a large `|p_mark - p_index|` could produce a fee larger than the premium stream itself, immediately draining PLP margins and creating a cascade of auto-closes. The floor ensures underwriters always earn at least `fee_base`. Derives from FR-007. |
| Test Strategy | Kontrol proof (`prove_funding_rate_bounds`) on the funding rate formula with symbolic `p_mark` and `p_index`. Fuzz test with extreme values including `p_index = 0`, large `|p_mark - p_index|`, and `alpha` at maximum. Unit test: assert `fee(t) == fee_max` when the adjustment term would exceed `fee_max - fee_base`. |
| References | FR-007, SC-007, SC-009 |

---

## INS-008: Protection Payoff Monotonicity

| Field | Value |
|-------|-------|
| ID | INS-008 |
| Description | A PLP's protection value is monotonically non-decreasing in `A_T`. As fee concentration increases (higher `A_T`, lower `B_T`), the protection position can only gain value or remain unchanged. It cannot lose value due to rising concentration. |
| Category | System-level |
| Formal Statement | For any two states with `A_T^(1) <= A_T^(2)` and all other parameters fixed: `protection_value(A_T^(1)) <= protection_value(A_T^(2))`. Equivalently, since `p_index = B_T / (1 - B_T)` and `B_T = 1 - A_T`: as `A_T` increases, `B_T` decreases, `p_index` decreases, and the CFMM price `p_mark` moves to reflect higher concentration exposure — increasing protection value. |
| Rationale | Monotonicity is the core economic guarantee to PLPs. Protection is only useful if it pays off precisely when the insured event (high concentration) occurs. If protection value fell when concentration rose, the product would provide negative insurance — the opposite of its intended purpose. Derives from SC-004. |
| Test Strategy | Fuzz test (`testFuzz_protection_monotone_in_AT`) with monotonically increasing `A_T` sequences, asserting protection value is non-decreasing at each step. Unit test with specific `A_T` trajectories including maximum concentration. Kontrol proof on the trading function's response to decreasing `p_index`. |
| References | FR-005, FR-006, SC-004, SC-008 |

---

## INS-009: Collateral Solvency

| Field | Value |
|-------|-------|
| ID | INS-009 |
| Description | The aggregate collateral held by all underwriter positions is at all times greater than or equal to the aggregate protection obligations owed to all registered PLP positions. The system is never in a state where it cannot pay out accrued protection. |
| Category | System-level |
| Formal Statement | At every state transition: `sum(collateral_i for all underwriter positions i) >= sum(protection_obligation_j for all PLP positions j)` where `protection_obligation_j` is the protection value accrued by PLP `j` that has not yet been settled. |
| Rationale | Solvency is the hardest and most critical invariant. An insolvent insurance system is worse than no system — it attracts PLPs who then cannot collect on protection. The invariant must hold after every operation including tick crossings, premium accruals, underwriter withdrawals, and oracle updates. Underwriter withdrawals are the primary risk vector and must validate this invariant before completing. Derives from FR-013 and the core insurance model. |
| Test Strategy | Fuzz test (`testFuzz_collateral_solvency`) over arbitrary sequences of deposits, withdrawals, concentration changes, and fee streams, asserting the aggregate inequality holds after every step. Unit test: attempt an underwriter withdrawal that would breach solvency and assert it reverts. Kontrol proof (`prove_collateral_solvency_maintained`) on the withdrawal guard. |
| References | FR-013, SC-008, SC-009 |

---

## INS-010: Fee Stream Cessation

| Field | Value |
|-------|-------|
| ID | INS-010 |
| Description | When a PLP's fee stream rate drops to exactly zero, the insurance position auto-close is triggered in the same hook callback. No position with a zero fee stream may remain open after the callback completes. |
| Category | Function-level |
| Formal Statement | `{fee_stream_rate[pos] == 0}` -> `afterFeeAccrual(pos)` -> `{pos.closed == true}`. The converse does not hold: a position may also close due to margin depletion (INS-002) while the fee stream is still nonzero. |
| Rationale | When fees stop, the PLP has no premium source — continuing the position would require them to post external collateral, which the system does not support. More importantly, the self-sizing hedge property (INS-003) requires insurance size to track fee stream rate; a zero-rate position with nonzero insurance size would violate proportionality. Derives from FR-010 and the streaming premium model described in spec clarifications. |
| Test Strategy | Unit test: register a PLP, simulate fee accrual, then zero out the fee stream, verify close triggers in the next callback. Kontrol proof (`prove_zero_stream_triggers_close`). Fuzz test with fee streams that reach zero at random points in a sequence, asserting no open positions survive a zero-rate callback. |
| References | FR-010, FR-016, SC-005, SC-006, SC-009 |
