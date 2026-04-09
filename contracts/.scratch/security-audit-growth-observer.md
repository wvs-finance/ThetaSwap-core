# Security Audit Report: Growth Observer Oracle System

## Project: ThetaSwap Growth Observer Oracle
## Auditor: Blockchain Security Auditor
## Date: 2026-04-09
## Scope Commit: thetaswap-patches branch

---

## Executive Summary

This audit covers the on-chain oracle system for recording cumulative LP reward growth
(globalGrowth from Angstrom protocol) into a ring buffer. The system comprises three
components: a `GrowthObservation` user-defined value type (bytes32-packed), a
`BlockNumberAwareGrowthObserverLib` providing record/query free functions over an
OpenZeppelin `CircularBuffer`, and an `AngstromAccumulatorOracleAdapter` that reads
Angstrom storage via `extsload`.

The review identified **2 Critical**, **3 High**, **2 Medium**, **3 Low**, and
**2 Informational** findings.

| Severity      | Count | Status       |
|---------------|-------|--------------|
| Critical      | 2     | Open         |
| High          | 3     | Open         |
| Medium        | 2     | Open         |
| Low           | 3     | Open         |
| Informational | 2     | Open         |

## Scope

| Contract / File                              | SLOC | Complexity |
|----------------------------------------------|------|------------|
| `GrowthObservation.sol`                      | 65   | Low        |
| `BlockNumberAwareGrowthObserverLib.sol`       | 55   | Medium     |
| `AngstromAccumulatorOracleAdapter.sol`        | 40   | Low        |

---

## Findings

### [C-01] No Access Control on `record()` -- Anyone Can Poison the Oracle

**Severity**: Critical
**Status**: Open
**Location**: `BlockNumberAwareGrowthObserverLib.sol#L16-L27` (free function),
`AngstromAccumulatorOracleAdapter.sol` (no `recordObservation()` yet)

**Description**:

The `record()` function is a free (file-level) function that writes to a
`CircularBuffer` in storage. It accepts arbitrary `_blockNumber` and
`_cumulativeGrowth` parameters with zero validation of their source. The adapter
contract currently has no `recordObservation()` entry point, but the user confirmed
one is planned.

If `recordObservation()` is implemented without access control, any address can:

1. Call `recordObservation()` with fabricated `_cumulativeGrowth` values
2. Insert observations with inflated or deflated growth to manipulate downstream
   consumers (e.g., a vault calculating LP yield)
3. Fill the ring buffer with garbage observations, evicting all legitimate data

Even if access control is added, the choice of *who* can call matters enormously.
If restricted to a single EOA, a compromised key drains the oracle. If restricted
to "anyone who pays gas" (permissionless keeper), the manipulation surface remains.

**Impact**:

Total corruption of the oracle. Any protocol consuming `observeGrowthDelta()` to
price LP positions, calculate insurance premiums, or distribute rewards would use
attacker-controlled data. Estimated impact: 100% of TVL dependent on this oracle.

**Proof of Concept**:

```solidity
// Attacker calls recordObservation() with inflated growth
adapter.recordObservation(poolId); // reads real globalGrowth = 1000
// Next block:
// Attacker front-runs legitimate keeper, calls with same block.number
// but the "at most one per block" dedup means the first caller wins.
// If attacker calls first with a manipulated adapter, they set the value.
```

**Recommendation**:

1. `recordObservation()` MUST have strict access control. Recommended: restrict to
   a trusted keeper address or a set of addresses controlled by a multisig/timelock.
2. The function should read `globalGrowth` internally (via `extsload`) rather than
   accepting it as a parameter. The current `globalGrowth(poolId)` view function on
   the adapter is the right pattern -- `recordObservation()` should call it internally
   so the value cannot be spoofed by the caller.
3. Consider a monotonicity check: `require(newGrowth >= latestGrowth)` to reject
   any observation where cumulative growth decreased.

---

### [C-02] Ring Buffer Not Initialized -- `setup()` Never Called

**Severity**: Critical
**Status**: Open
**Location**: `AngstromAccumulatorOracleAdapter.sol` (entire contract),
`BlockNumberAwareGrowthObserverLib.sol#L26`

**Description**:

The `AngstromAccumulatorOracleAdapter` does not declare a `CircularBuffer` storage
variable, and does not call `CircularBuffer.setup()` anywhere. The
`BlockNumberAwareGrowthObserverLib` functions expect a properly initialized buffer.

Without `setup()`, `self._data.length` is 0, and `push()` will attempt
`index % 0` which is a division-by-zero panic. The entire oracle is non-functional
until this is resolved.

**Impact**:

Complete denial of service. No observations can be recorded. Any call to `record()`
reverts with a panic.

**Recommendation**:

1. Add a `CircularBuffer.Bytes32CircularBuffer` storage variable to the adapter.
2. Call `CircularBuffer.setup(buffer, SIZE)` in the constructor or an initializer.
3. Choose `SIZE` carefully -- it determines the maximum historical lookback window.
   For example, SIZE=8640 covers ~24 hours at 10s blocks on L1.

---

### [H-01] `uint208` Truncation Will Eventually Overflow for Q128.128 Accumulators

**Severity**: High
**Status**: Open
**Location**: `GrowthObservation.sol#L30-L37`, specifically `SafeCastLib.toUint208()`

**Description**:

Angstrom's `globalGrowth` is a `uint256` value in Q128.128 fixed-point format
(128 integer bits + 128 fractional bits). The observation packs this into `uint208`,
which provides Q80.128 -- only 80 bits for the integer part.

The maximum `uint208` value is `2^208 - 1`. For a Q128.128 accumulator, the integer
part (bits above the 128 fractional bits) is limited to `2^80 - 1` which is
approximately `1.2 * 10^24`.

**Overflow timeline analysis**:

The `globalGrowth` accumulator increases by `reward / totalLiquidity` each epoch
(in Q128.128). The rate depends on:
- Total rewards distributed per epoch
- Total active liquidity

For a pool with $10M TVL distributing $100K/day in rewards:
- Daily growth in Q128.128 integer part: ~0.01 * 2^128 = ~3.4 * 10^36

This would overflow `uint80` in the *first observation*. The `SafeCastLib.toUint208()`
will revert, permanently bricking the oracle for any pool with meaningful cumulative
growth.

**However**, the actual overflow depends on how Angstrom computes `globalGrowth`.
If the accumulator uses wrapping arithmetic (as Uniswap V3 fee accumulators do),
values cycle through the full `uint256` range and `toUint208()` will revert as
soon as the value exceeds `2^208`.

**Impact**:

The oracle becomes permanently non-functional for any pool where `globalGrowth`
exceeds `2^208`. The `SafeCastLib.toUint208()` reverts, meaning `record()` reverts,
meaning no new observations can be written. This is a time bomb.

**Recommendation**:

Two options:

**Option A (Preferred)**: Store the full `uint256` globalGrowth and use a 2-slot
observation (bytes32 for blockNumber + padding, bytes32 for growth). The ring buffer
already stores `bytes32` values -- use two consecutive entries per observation, or
switch to a custom ring buffer with `uint256` values.

**Option B**: Store only the lower 208 bits and handle wraparound in delta
computation. This works if:
- `growthDelta()` uses unchecked subtraction (it already does)
- Both observations are within `2^208` of each other (true if observations are
  frequent enough relative to growth rate)

The current `unchecked` subtraction in `growthDelta()` (line 59) already handles
wraparound correctly for modular arithmetic. But `newGrowthObservation()` will
revert before the value is stored. Replace `SafeCastLib.toUint208()` with a simple
`uint208(_cumulativeGrowth)` truncation if Option B is chosen, and document the
wraparound assumption.

---

### [H-02] Binary Search Assumes Strict Monotonicity of Block Numbers -- No Duplicate Block Handling

**Severity**: High
**Status**: Open
**Location**: `BlockNumberAwareGrowthObserverLib.sol#L47-L62`

**Description**:

The `record()` function deduplicates by block number (line 24: skips if latest
observation has same block number). However, the binary search in `observeAt()` does
not handle the case where multiple observations share the same block number (which
cannot happen given the dedup, but could if the dedup is bypassed or if the buffer
is used by multiple callers).

More critically, the binary search assumes that `last(0)` has the highest block
number and `last(total-1)` has the lowest. This is guaranteed by the CircularBuffer
semantics (LIFO order via `last()`) combined with the assumption that
`block.number` is monotonically increasing and `record()` is called with increasing
block numbers.

**Attack scenario**: If an attacker can call `record()` with an out-of-order
`_blockNumber` (e.g., passing `block.number - 100`), the binary search invariant
breaks. The function would return incorrect observations or revert unexpectedly.

**Impact**:

If `_blockNumber` is passed as a parameter (rather than read from `block.number`),
an attacker can insert out-of-order observations that corrupt the binary search.
Even if `record()` always uses `block.number`, an L2 sequencer could manipulate
block numbers (see L-01).

**Recommendation**:

1. `record()` should enforce monotonicity: `require(_blockNumber > latest.blockNumber())`
   (not just equality check, but strictly greater than).
2. Hardcode `block.number` in the adapter's `recordObservation()` rather than
   accepting it as a parameter.

---

### [H-03] `growthDelta()` Unchecked Subtraction Returns Incorrect Results on Non-Monotonic Input

**Severity**: High
**Status**: Open
**Location**: `GrowthObservation.sol#L57-L61`

**Description**:

```solidity
function growthDelta(GrowthObservation earlier, GrowthObservation later) pure returns (uint208) {
    unchecked {
        return later.cumulativeGrowth() - earlier.cumulativeGrowth();
    }
}
```

The `unchecked` subtraction means if `later.cumulativeGrowth() < earlier.cumulativeGrowth()`,
the result wraps around to a massive `uint208` value instead of reverting.

The NatSpec says "assumes `later` was recorded after `earlier` (monotonic accumulator)".
However, `observeGrowthDelta()` in the observer library calls this with observations
looked up by block number -- there is no runtime enforcement that the growth values
are actually monotonic.

**Scenarios where monotonicity breaks**:

1. A bug in Angstrom's reward accounting (has happened in other protocols)
2. Storage slot derivation error in the adapter reading the wrong slot
3. An upgrade to Angstrom that resets or modifies the accumulator

In any of these cases, `growthDelta()` silently returns a garbage value close to
`2^208` instead of reverting.

**Impact**:

Downstream consumers receive wildly inflated growth deltas. A vault using this to
calculate LP yield would compute astronomical returns and potentially distribute
far more tokens than earned.

**Recommendation**:

Add a checked mode or at minimum validate the result:

```solidity
function growthDelta(GrowthObservation earlier, GrowthObservation later) pure returns (uint208) {
    uint208 laterGrowth = later.cumulativeGrowth();
    uint208 earlierGrowth = earlier.cumulativeGrowth();
    require(laterGrowth >= earlierGrowth, "Non-monotonic growth");
    unchecked {
        return laterGrowth - earlierGrowth;
    }
}
```

If intentional wrapping arithmetic is desired (Option B from H-01), document this
explicitly and ensure all consumers understand the modular semantics.

---

### [M-01] First-Caller-Wins Per Block Creates Frontrunning Opportunity

**Severity**: Medium
**Status**: Open
**Location**: `BlockNumberAwareGrowthObserverLib.sol#L22-L25`

**Description**:

```solidity
if (total > 0) {
    GrowthObservation latest = GrowthObservation.wrap(CircularBuffer.last(buffer,0));
    if (latest.blockNumber() == uint48(_blockNumber)) return;
}
```

The deduplication logic records at most one observation per block, keeping the
*first* one. An attacker who front-runs the legitimate keeper within the same block
can ensure their (potentially stale or manipulated) observation is recorded while
the legitimate one is silently discarded.

**Attack scenario**:

1. Attacker monitors the mempool for `recordObservation()` transactions
2. Attacker front-runs with higher gas, calling `recordObservation()` at the start
   of the block when `globalGrowth` has not yet been updated by Angstrom's bundle
3. The legitimate keeper's transaction arrives later in the same block but is
   silently skipped
4. The recorded observation contains a stale `globalGrowth` value

This is especially relevant because Angstrom settles bundles on L1 -- the
`globalGrowth` value changes within a block when the Angstrom bundle executes. An
observation recorded *before* the bundle in the same block captures pre-bundle growth.

**Impact**:

Systematic underreporting of growth by one bundle's worth per observation. Over time,
this accumulates into significant under-measurement of LP rewards.

**Recommendation**:

1. Use last-caller-wins instead of first-caller-wins (overwrite the observation if
   same block number)
2. Or restrict `recordObservation()` to only be callable in a specific context
   (e.g., as part of the Angstrom bundle settlement callback)

---

### [M-02] DoS via Buffer Eviction -- Attacker Can Erase Historical Observations

**Severity**: Medium
**Status**: Open
**Location**: `BlockNumberAwareGrowthObserverLib.sol#L26`,
OZ `CircularBuffer.sol#L89-L93`

**Description**:

The CircularBuffer has a fixed size. When full, `push()` overwrites the oldest entry.
If `record()` has no access control (see C-01), an attacker can:

1. Wait until the buffer is nearly full with legitimate observations
2. Call `record()` repeatedly across consecutive blocks to push new entries
3. Each push evicts the oldest legitimate observation
4. After `SIZE` blocks, all legitimate historical data is gone

Even with access control, a malicious keeper could rapidly fill the buffer with
observations at every block, reducing the effective time window covered by the buffer.

**Impact**:

Loss of historical observation data. Any consumer needing lookback beyond the
attacker-controlled window gets `ObservationExpired` reverts. This could break
time-weighted calculations or insurance pricing that requires longer lookback periods.

**Recommendation**:

1. Access control on `record()` is the primary mitigation (see C-01)
2. Consider minimum spacing between observations (e.g., record at most once per
   N blocks) to maximize the time window covered by the buffer
3. Size the buffer generously relative to the maximum lookback needed

---

### [L-01] `block.number` Unreliable on L2 -- Oracle Breaks on Rollups

**Severity**: Low
**Status**: Open
**Location**: `BlockNumberAwareGrowthObserverLib.sol#L18` (accepts `_blockNumber` param)

**Description**:

The system packs block numbers into `uint48`, which is sufficient for L1 (current
block ~22M, `uint48` max ~281 trillion). However:

1. On Optimism, `block.number` was the L1 block number pre-Bedrock but is now
   the L2 block number (1-second blocks). At 1 block/sec, `uint48` overflows in
   ~8.9 million years -- safe.
2. On Arbitrum, `block.number` is the L1 block number by default, but Arbitrum
   Nitro supports sub-second blocks with separate numbering.
3. On some L2s, block numbers can be set by the sequencer and may not be strictly
   monotonic or may have gaps.

The bigger issue: Angstrom is designed for L1 settlement. If this oracle adapter is
deployed on an L2 but reads `globalGrowth` from an L1 Angstrom contract via a
bridge, the block numbers would be mismatched (L2 block number stored alongside L1
growth data).

**Recommendation**:

1. Document that this oracle is L1-only
2. If L2 support is needed, use `block.timestamp` instead of `block.number`
3. Add a comment to `record()` that `_blockNumber` should be `block.number`

---

### [L-02] `observeAt()` Returns "At or Before" Semantics -- May Return Stale Data

**Severity**: Low
**Status**: Open
**Location**: `BlockNumberAwareGrowthObserverLib.sol#L29-L63`

**Description**:

`observeAt(targetBlock)` returns the observation at or before `targetBlock`. If the
buffer has observations at blocks [100, 200, 300] and the caller requests block 250,
they get the observation from block 200 -- which could be 50 blocks stale.

This is standard for discrete oracle systems (Uniswap V3 does the same), but
consumers must be aware that the returned growth value may not reflect the actual
growth at `targetBlock`. The gap between the returned observation's block and
`targetBlock` can be arbitrarily large if observations are sparse.

**Recommendation**:

1. Consider adding an interpolation function that linearly interpolates between
   the surrounding observations (as Uniswap V3 does with its TWAP oracle)
2. At minimum, return the observation's block number alongside the growth value
   so consumers can assess staleness

---

### [L-03] `elapsedBlocks()` and Comparison Functions Use Unchecked Arithmetic

**Severity**: Low
**Status**: Open
**Location**: `GrowthObservation.sol#L64-L68`, `L76-L100`

**Description**:

`elapsedBlocks()` uses unchecked subtraction. If called with `earlier` having a
higher block number than `later`, it wraps around. The comparison functions (`gte`,
`lt`) also use unchecked blocks, though these simply compare `uint48` values which
cannot overflow in comparisons.

The `elapsedBlocks()` wraparound is the only real concern, and it mirrors the
`growthDelta()` issue. However since `elapsedBlocks()` is not currently called by
the observer library, the risk is limited to future consumers.

**Recommendation**:

Add checked variants or document the ordering requirement prominently.

---

### [I-01] `REWARD_GROWTH_SIZE` Magic Number -- Potential Slot Derivation Mismatch

**Severity**: Informational
**Status**: Open
**Location**: `AngstromAccumulatorOracleAdapter.sol#L12`

**Description**:

`REWARD_GROWTH_SIZE = 16777216` (2^24) is hardcoded in the adapter. This must
exactly match the array size in `PoolRewards.rewardGrowthOutside`. It does match
the current Angstrom code (`PoolRewards.sol#L10`), but if Angstrom upgrades and
changes this constant, the adapter will read the wrong storage slot for
`globalGrowth`.

The slot calculation for `globalGrowth` is:
`base + REWARD_GROWTH_SIZE` where `base` is the mapping slot for the pool. If
`REWARD_GROWTH_SIZE` changes in Angstrom, this adapter silently reads garbage.

**Recommendation**:

Add a deployment-time or runtime validation that the slot derivation returns the
expected value (e.g., compare with a known reference pool's growth).

---

### [I-02] `growthInside()` Unchecked Subtraction Mirrors Angstrom Semantics But Lacks Guard

**Severity**: Informational
**Status**: Open
**Location**: `AngstromAccumulatorOracleAdapter.sol#L45-L54`

**Description**:

The `growthInside()` function replicates `PoolRewardsLib.getGrowthInside()` using
unchecked subtraction. This is correct for Uniswap-style growth-outside accounting
where values are expected to wrap. However, it reads raw storage slots via `extsload`
and has no ability to validate that the values are well-formed.

If the slot derivation is wrong (see I-01), the unchecked subtraction on garbage
values produces garbage output without reverting.

**Recommendation**:

Consider adding sanity bounds on the raw values read from `extsload`, or at minimum
document that consumers should validate the output against expected ranges.

---

## Appendix

### A. CircularBuffer Wraparound Analysis

The OZ `CircularBuffer.last(i)` function (v5.1.0) uses:
```solidity
return Arrays.unsafeAccess(self._data, (index - i - 1) % modulus).value;
```

Where `index = self._count` (total pushes ever, not capped) and `modulus = self._data.length`.

This correctly handles wraparound. When the buffer is full:
- `last(0)` = most recent push = `_data[(_count - 1) % size]`
- `last(size - 1)` = oldest surviving push = `_data[_count % size]`

The binary search in `observeAt()` iterates over `last(0)` through `last(total-1)`,
which is always in reverse-chronological order. This is correct **provided**
observations are always pushed in increasing block-number order.

**Verdict**: The ring buffer wraparound is handled correctly by the OZ library.
The binary search correctly uses `last()` semantics. No bug here.

### B. Reentrancy Analysis

- `record()` writes to storage (CircularBuffer.push) but makes no external calls.
  No reentrancy vector.
- `observeAt()` and `observeGrowthDelta()` are `view` functions. No reentrancy vector.
- `extsload()` is a `view` function (STATICCALL). No reentrancy vector.
- The adapter's `globalGrowth()` and `growthInside()` are `view` functions making
  STATICCALL to Angstrom and PoolManager. No reentrancy vector.

**Verdict**: No reentrancy vectors identified in the current codebase.

### C. Truncation Overflow Timeline (uint208 for Q128.128)

The Q128.128 format uses 128 bits for the integer part. uint208 stores 208 bits
total. After removing 128 fractional bits, the integer capacity is 80 bits.

`2^80 = 1,208,925,819,614,629,174,706,176`

For context, if `globalGrowth` represents cumulative reward per unit of liquidity
in Q128.128, and rewards are denominated in wei (10^18 per token):
- `1 token per liquidity unit` in Q128.128 = `10^18 * 2^128 = 3.4 * 10^56`
- This **already exceeds** `2^208 = 4.1 * 10^62` ... wait, let me recalculate.
- `2^208 = 411,376,139,330,301,510,538,742,295,639,337,626,245,683,966,408,394,965,837,152,256`
- `10^18 * 2^128 = 340,282,366,920,938,463,463,374,607,431,768,211,456 * 10^18 = 3.4 * 10^56`
- `2^208 / (10^18 * 2^128) = 2^208 / (2^128 * 10^18) = 2^80 / 10^18 = ~1.2 * 10^6`

So the accumulator overflows uint208 after distributing roughly **1.2 million tokens
per unit of liquidity** cumulatively. Whether this is safe depends entirely on the
token denomination and pool lifetime. For pools that run for years with high reward
rates, this is a real concern.

### D. Methodology

1. Manual line-by-line code review of all three files
2. Analysis of OZ CircularBuffer v5.1.0 internals
3. Verification of Solady SafeCastLib behavior
4. Cross-reference with Angstrom core contract storage layout
5. Analysis of slot derivation correctness
6. Threat modeling for oracle manipulation, frontrunning, and DoS
7. Mathematical analysis of uint208 overflow timeline

---

## Priority Remediation Order

1. **C-01**: Add access control to `recordObservation()` and read `globalGrowth`
   internally -- this is a showstopper
2. **C-02**: Initialize the CircularBuffer -- the oracle literally does not work
   without this
3. **H-01**: Resolve the uint208 truncation -- either use full uint256 or document
   and handle wrapping explicitly by removing SafeCastLib
4. **H-02**: Enforce strict monotonicity of block numbers in `record()`
5. **H-03**: Add a checked subtraction option to `growthDelta()`
6. **M-01**: Switch to last-caller-wins for same-block dedup
7. **M-02**: Add access control as primary DoS mitigation
8. Medium and Low findings can ship with monitoring if the above are resolved.
