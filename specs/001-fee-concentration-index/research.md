# Research: Fee Concentration Index

## R1: Tick Range Lookup Strategy on afterSwap

**Decision**: Use Uniswap V4's tick bitmap via `StateLibrary.getTickBitmap()` to walk initialized ticks in the swap's traversed range. Each initialized tick boundary maps to position groups registered in the TickRangePositionSet.

**Rationale**: The V4 tick bitmap is already maintained by the pool — no extra storage cost. `getTickBitmap(manager, poolId, wordPos)` returns a 256-bit word where each bit represents an initialized tick. By reading the bitmap words covering [tick_before, tick_after], we can identify which initialized ticks were crossed. Each such tick is either a tickLower or tickUpper of a registered position group.

**Alternatives considered**:
- Maintaining a separate sorted structure of tick range endpoints: rejected because it duplicates V4's bitmap and costs extra storage.
- Only tracking positions at the current active tick: rejected because it misses positions whose ranges the swap crosses through.

**Implementation note**: `nextInitializedTickWithinOneWord()` is an internal library function operating on the storage mapping directly — NOT exposed via StateLibrary. For hook use, we read bitmap words via `StateLibrary.getTickBitmap()` and do bit manipulation with `BitMath.mostSignificantBit()` / `leastSignificantBit()` to walk initialized ticks.

## R2: Position Identification on Hook Callbacks

**Decision**: Use the `PoolKey` + `ModifyLiquidityParams` (tickLower, tickUpper, salt) provided in hook callback data to derive a position key via `keccak256(abi.encode(owner, tickLower, tickUpper, salt))`. This is the same key Uniswap V4 uses internally.

**Rationale**: The hook's `afterAddLiquidity` and `afterRemoveLiquidity` callbacks receive `ModifyLiquidityParams` which contains tickLower, tickUpper, and salt. Combined with msg.sender (the PositionManager), this uniquely identifies the position.

**Alternatives considered**:
- Using tokenId from PositionManager: rejected because it requires an external call and is periphery-specific.
- Using a sequential ID: rejected because it doesn't map to V4's internal position tracking.

## R3: Fee Growth Reading from StateLibrary

**Decision**: Use `StateLibrary.getFeeGrowthInside(manager, poolId, tickLower, tickUpper)` to get per-position fee growth, and `StateLibrary.getFeeGrowthGlobal(manager, poolId)` for global fee growth. The ratio x_k = feeGrowthInside / feeGrowthGlobal.

**Rationale**: StateLibrary provides direct external access to pool state via `extsload`. These are view calls with no state mutation.

**Key detail**: `feeGrowthInside` is returned as two uint256 values (feeGrowthInside0X128, feeGrowthInside1X128) — one per token. The fee share ratio x_k should use the token that is the numeraire (token Y in the CFMM specification). Which token is the numeraire is determined at deployment.

**Alternatives considered**:
- Computing feeGrowthInside manually from tick-level data: rejected because StateLibrary already provides it.
- Using both tokens' fee growth: deferred — v1 uses single-token numeraire fee growth.

## R4: Q128 Fixed-Point Arithmetic for Fee Share Ratio

**Decision**: Store x_k as Q128 (uint256 with 128 fractional bits). Division feeGrowthInside / feeGrowthGlobal produces a Q128 result. Squaring x_k^2 fits in uint256 because Q128 * Q128 = Q256 which requires a 512-bit intermediate — use `mulDiv` from solady or manual `mul512` followed by right-shift.

**Rationale**: Uniswap V4's feeGrowthInsideX128 is already Q128 format. The global feeGrowth is also Q128. Dividing two Q128 values produces a Q0 (dimensionless ratio in [0,1]). To preserve precision, we left-shift the numerator by 128 bits before dividing, producing a Q128 result.

**Overflow analysis**:
- x_k is in [0, 1], stored as Q128: max value = 2^128
- x_k^2: max = 2^256 — fits in uint256 ONLY if we accept Q256 result
- Better: use `FullMath.mulDiv(x_k, x_k, 2^128)` to get x_k^2 in Q128, avoiding overflow
- theta_k = 1/lifetime: stored as Q128 where lifetime >= 1, so theta_k in [0, 1] as Q128
- theta_k * x_k^2: Q128 * Q128 → use mulDiv to keep result in Q128
- accumulatedSum: Q128, accumulates additively

**Alternatives considered**:
- Q96 (matching sqrtPriceX96): rejected because feeGrowth is Q128, requiring conversion that loses precision.
- Q64: rejected because insufficient precision for small fee shares.

## R5: Square Root for Lazy Index Computation

**Decision**: Use an integer sqrt implementation (e.g., from solady `FixedPointMathLib.sqrt()` or a Newton's method implementation) to compute A_T = sqrt(accumulatedSum) on read.

**Rationale**: The accumulatedSum is in Q128. sqrt(Q128) = Q64. To get A_T in a useful precision, we first left-shift accumulatedSum by 128 bits (to Q256), then sqrt gives Q128 result. This preserves the Q128 convention.

**Gas estimate**: sqrt via Newton's method is ~200-500 gas. Acceptable for a view function.

**Alternatives considered**:
- Storing A_T directly on each update: rejected because sqrt on every afterRemoveLiquidity is wasteful.
- Babylonian method vs lookup table: deferred to implementation — both produce correct results.

## R6: TickRangePositionSet Data Structure

**Decision**: Use a nested mapping: `mapping(bytes32 rangeKey => mapping(bytes32 positionKey => bool))` where `rangeKey = keccak256(abi.encode(tickLower, tickUpper))`. Additionally maintain a count per range key for empty-set detection, and a reverse mapping from positionKey to rangeKey for O(1) cleanup on removal.

**Rationale**: Solidity mappings provide O(1) lookup and deletion. The count allows O(1) empty-set detection without iterating. The reverse mapping avoids needing to pass tick range info at removal time (though it's available in callback params).

**Gas analysis**:
- Register (afterAddLiquidity): 1 SSTORE (set bool) + 1 SSTORE (increment count) + 1 SSTORE (reverse mapping) = ~60k gas
- Deregister (afterRemoveLiquidity): 1 SSTORE (clear bool) + 1 SSTORE (decrement count) + 1 SSTORE (clear reverse) = ~15k gas (refunds)
- Lookup (afterSwap): 1 SLOAD per position in range = ~2.1k gas each

**Alternatives considered**:
- EnumerableSet from OpenZeppelin: rejected because iteration is not needed — we walk via tick bitmap.
- Array with index mapping: rejected because deletion requires swapping, adding complexity.

**Open question**: On afterSwap, we need to iterate all positions in a given tick range to increment their swap counts. The mapping-based approach doesn't support iteration. We need an additional structure — either a linked list of position keys per range, or an array. An array per range key with a positionKey→index mapping for O(1) deletion is the practical choice.

**Revised decision**: `mapping(bytes32 rangeKey => bytes32[] positionKeys)` + `mapping(bytes32 positionKey => uint256 indexInArray)` for O(1) add/remove and sequential iteration on afterSwap.
