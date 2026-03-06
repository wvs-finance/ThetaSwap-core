# Feature Specification: ThetaSwap Fee Concentration Insurance CFMM

**Feature Branch**: `002-theta-swap-cfmm`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "Standalone piecewise-linear CLAMM for fee concentration derivatives: implements trading function y = x - ln(x) - 1 with Uniswap V3-style tick array, single collateral, concentrated liquidity, per-swap funding rate, reading B_T from FeeConcentrationIndex V4 hook via getIndex()"

## Clarifications

### Session 2026-03-04

- Q: What is the economic framing of the derivative market? → A: Insurance premium model. PLPs buy protection against fee concentration; underwriters (speculators/yield seekers) sell protection and collect premiums. JITs are not required as counterparties.
- Q: How should insurance settlement work? → A: Streaming premium. Buyers pay an ongoing collateral stream as premium and receive continuous protection. Premium rate priced by the CFMM trading function.
- Q: How should margin depletion be handled? → A: Auto-close. System automatically closes positions when margin hits minimum threshold. No external keeper needed.
- Q: How should the fee-to-premium pipeline work? → A: Hook-integrated auto-deduction. PLPs' V4 fee accruals are the premium source. A companion V4 hook automatically routes a fraction of each PLP's accrued fees to the insurance CFMM. No manual claim step. Collateral IS the fee stream — when fees stop, insurance stops. This creates a self-sizing hedge: insurance size scales proportionally with fee exposure.
- Q: How should the insurance CFMM relate to the existing FeeConcentrationIndex hook? → A: Companion hook. A second V4 hook (ThetaSwapInsurance) reads from FeeConcentrationIndex and handles fee routing + insurance CFMM state. FeeConcentrationIndex remains unchanged from the 001 branch.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - PLP Buys Fee Concentration Protection (Priority: P1)

A passive liquidity provider (PLP) in a Uniswap V4 pool opts into fee concentration insurance. The companion hook automatically deducts a fraction of their accruing V4 fees as streaming premium. In return, the PLP receives continuous protection: their position appreciates when fee concentration rises (A_T increases), offsetting the loss of fee income caused by JIT crowding.

**Why this priority**: Core value proposition. PLPs are the natural buyers — their fee stream IS the premium. Without this flow, the insurance market has no demand side.

**Independent Test**: Can be fully tested by registering a PLP's V4 position with the insurance hook, simulating fee accrual and concentration changes, and verifying that premium streams out and protection value accrues correctly.

**Acceptance Scenarios**:

1. **Given** a PLP with an active V4 liquidity position earning fees, **When** they register with the ThetaSwapInsurance hook, **Then** a fraction of their accruing fees begins streaming to the insurance CFMM as premium, and a protection position is opened.
2. **Given** a registered PLP whose fee stream is active, **When** fee concentration A_T increases (B_T decreases), **Then** the PLP's protection position appreciates in value, offsetting reduced fee income.
3. **Given** a registered PLP whose V4 position stops earning fees (removed liquidity or fully crowded out), **When** the fee stream drops to zero, **Then** the insurance position auto-closes and any remaining margin is returned.

---

### User Story 2 - Underwriter Provides Insurance Backing (Priority: P1)

A speculator or yield seeker deposits collateral as an underwriter in a specific tick range [tickLower, tickUpper] of the insurance CFMM. They earn streaming premiums from PLPs' fee deductions. They bear risk: their backing decreases when fee concentration rises.

**Why this priority**: Equal to P1 — insurance requires underwriters. The CFMM cannot price protection without a supply side.

**Independent Test**: Can be tested by depositing collateral into a tick range, verifying the position earns premiums from PLP fee streams, and withdrawing to verify collateral + earned premiums are returned.

**Acceptance Scenarios**:

1. **Given** an initialized insurance CFMM with active PLP premium streams, **When** an underwriter deposits collateral into range [tickLower, tickUpper], **Then** a concentrated liquidity position is created and begins earning streaming premium proportional to its liquidity share.
2. **Given** an underwriter position earning premiums, **When** fee concentration rises (A_T increases), **Then** the underwriter's backing decreases (they pay protection to PLPs), partially offset by premiums earned.
3. **Given** an underwriter position, **When** they remove liquidity, **Then** they receive remaining collateral plus net accrued premiums minus protection payouts.

---

### User Story 3 - Initialize Insurance Pool (Priority: P2)

A pool creator initializes a ThetaSwap insurance pool for a specific V4 pool by deploying the ThetaSwapInsurance companion hook, linking it to the FeeConcentrationIndex hook, and setting parameters (fee_base, fee_max, alpha, tick spacing, premium fraction).

**Why this priority**: Required setup before any PLP registration or underwriter activity, but happens once per pool.

**Independent Test**: Can be tested by deploying the companion hook and verifying it correctly reads from FeeConcentrationIndex and initializes CFMM state.

**Acceptance Scenarios**:

1. **Given** a deployed FeeConcentrationIndex hook tracking a V4 pool, **When** a pool creator deploys and initializes the ThetaSwapInsurance companion hook, **Then** the insurance CFMM state is initialized with the specified parameters and linked to the FeeConcentrationIndex oracle.
2. **Given** an already-initialized insurance pool for a given PoolKey, **When** someone attempts to initialize again, **Then** the transaction reverts.

---

### User Story 4 - Query Insurance State (Priority: P3)

An observer queries the current state: mark price, index price, active premium rate, PLP protection values, underwriter positions, and pool-level metrics.

**Why this priority**: Essential for UX but not for core functionality.

**Independent Test**: Can be tested by calling view functions after operations and verifying returned values match expected state.

**Acceptance Scenarios**:

1. **Given** an active insurance pool, **When** an observer queries the premium rate, **Then** the returned value reflects the current streaming rate derived from the funding formula and active fee flows.
2. **Given** an active insurance pool, **When** an observer queries a PLP's protection value, **Then** the returned value reflects accrued protection based on concentration changes since registration.

---

### Edge Cases

- What happens when B_T = 0 (full concentration)? p_index = 0. The CFMM handles p_index = 0 without division by zero. Protection positions are at maximum value.
- What happens when B_T approaches 1 (no concentration)? p_index → ∞. The system caps p_index at the maximum tick price. Protection positions are near zero value (nothing to insure against).
- What happens when a PLP's fee stream fluctuates rapidly? Premium deduction tracks actual fee accrual — no smoothing. Insurance size adjusts in real-time.
- What happens when the FeeConcentrationIndex hook is unreachable? The companion hook reverts rather than using stale data.
- What happens when no underwriters exist? PLPs cannot register for protection (no supply side). Premium rate would be infinite — system requires minimum underwriter liquidity.
- What happens when a PLP removes their V4 liquidity? Fee stream stops → premium stops → insurance auto-closes. Remaining margin returned.
- What happens when x approaches 0 in the trading function? ln(x) → -∞ and y → ∞. The tick array has a maximum tick that bounds the price range.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement the trading function `y = x - ln(x) - 1` using piecewise-linear approximations aligned to a tick array with configurable tick spacing.
- **FR-002**: System MUST support concentrated liquidity where underwriters deposit collateral into discrete tick ranges `[tickLower, tickUpper]`.
- **FR-003**: System MUST be deployed as a companion V4 hook (ThetaSwapInsurance) that reads from the existing FeeConcentrationIndex hook without modifying it.
- **FR-004**: System MUST read the fee dispersion index B_T by calling `IFeeConcentrationIndex.getIndex()` on the linked FeeConcentrationIndex hook.
- **FR-005**: System MUST compute the index price as `p_index = B_T / (1 - B_T)` from the oracle-provided B_T value.
- **FR-006**: System MUST compute the mark price as `p_mark = (1 - x) / x` from the CFMM's current active virtual reserves.
- **FR-007**: System MUST apply a per-swap funding rate: `fee(t) = fee_base + sign(p_mark - p_index) · min(α · |p_mark - p_index| / (p_index + 1), fee_max - fee_base)`.
- **FR-008**: System MUST auto-deduct a configurable fraction of each registered PLP's V4 fee accruals as streaming premium, routing it to the insurance CFMM.
- **FR-009**: System MUST allow PLPs to register their V4 position for insurance, linking their fee stream as premium source.
- **FR-010**: System MUST auto-close PLP protection positions when their fee-funded margin reaches a minimum threshold or when their fee stream drops to zero.
- **FR-011**: System MUST accrue streaming premiums to underwriter positions per-tick proportional to each underwriter's liquidity share.
- **FR-012**: System MUST handle tick crossings during premium/protection rebalancing by updating active liquidity and switching to the next tick's linear coefficients.
- **FR-013**: System MUST allow underwriters to add and remove liquidity at any time, computing collateral amounts from current virtual reserves and accrued premiums.
- **FR-014**: System MUST revert operations if the FeeConcentrationIndex oracle call fails.
- **FR-015**: System MUST bound the price domain with minimum and maximum ticks to prevent overflow from extreme values of ln(x).
- **FR-016**: System MUST ensure insurance position size scales proportionally with the PLP's fee stream (self-sizing hedge property).

### Key Entities

- **Insurance Pool**: A CFMM instance identified by V4 PoolKey. Holds fee parameters (fee_base, fee_max, α), tick spacing, premium fraction, link to FeeConcentrationIndex hook, and current tick/price state.
- **PLP Protection Position**: A registered PLP's insurance position. Linked to their V4 position ID. Tracks: fee stream rate, premium paid, protection value accrued, remaining margin (accumulated fees minus streamed premiums). Auto-closes when margin depleted or fee stream stops.
- **Underwriter Position**: An underwriter's collateral commitment to a tick range [tickLower, tickUpper]. Tracks: liquidity amount, premium earned, protection payouts owed, fee growth snapshots.
- **Tick**: A discrete price point in the tick array. Stores net liquidity delta (underwriter liquidity entering/leaving), premium growth accumulators, and piecewise-linear coefficients (slope, intercept) for the local ln(x) approximation.
- **Virtual Reserves**: Internal (x, y) values representing the CFMM state. x is the "risky" reserve (concentration exposure), y is the "numeraire" reserve. Not externally held — all settlement flows through fee deductions (PLPs) and collateral deposits (underwriters).
- **Oracle State**: The most recent B_T value read from FeeConcentrationIndex, and the derived p_index. Refreshed on every hook callback.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Piecewise-linear approximation of `y = x - ln(x) - 1` produces swap amounts with relative error below 10^-8 compared to the exact curve within each tick.
- **SC-002**: Multi-tick operations crossing N tick boundaries correctly update active liquidity and switch linear coefficients at each crossing.
- **SC-003**: Underwriter positions earn premiums proportional to their liquidity share, with zero premium leakage to positions outside the active tick range.
- **SC-004**: PLP protection positions appreciate correctly when A_T increases, with payoff matching the trading function's reserve curve within piecewise-linear error bounds.
- **SC-005**: Self-sizing hedge property holds: insurance position size tracks PLP fee stream rate within one hook callback of fee accrual changes.
- **SC-006**: Auto-close triggers correctly when PLP margin reaches minimum threshold, returning remaining margin with zero loss beyond accrued premiums.
- **SC-007**: The funding rate mechanism drives `|p_mark - p_index| → 0` over a sequence of arbitrage-incentivized operations, converging within 10 cycles for deviations up to 50%.
- **SC-008**: All 31 invariants from the mathematical model (specs/model/invariants.tex) hold under fuzz testing with 10,000+ runs.
- **SC-009**: The system correctly handles all edge cases (B_T = 0, B_T → 1, zero underwriter liquidity, oracle failure, fee stream cessation) without panics or undefined behavior.

## Assumptions

- The FeeConcentrationIndex V4 hook (001 branch) is deployed and actively tracking a V4 pool before the companion hook is deployed.
- The FeeConcentrationIndex hook is not modified — the companion hook interacts with it via its public `getIndex()` interface only.
- V4 allows multiple hooks on the same pool, or the companion hook wraps/composes with the existing hook via V4's hook architecture.
- The collateral deposited by underwriters is a standard ERC20 (e.g., USDC, WETH) with no fee-on-transfer or rebasing mechanics.
- PLP fee accruals are accessible to the companion hook via V4's fee growth accounting (StateLibrary).
- Tick spacing follows the Uniswap V3 convention: `p_i = 1.0001^i`.
- The piecewise-linear coefficients (slope, intercept) per tick are computed at initialization and cached in storage.
