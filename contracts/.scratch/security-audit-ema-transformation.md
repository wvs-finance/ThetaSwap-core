# Security Audit: EMAGrowthTransformationLib.sol

**Auditor:** Blockchain Security Auditor
**Date:** 2026-04-09
**Commit:** thetaswap-patches (pre-merge)
**Scope:** Single file -- `src/libraries/transformations/EMAGrowthTransformationLib.sol`

---

## Summary

| Severity      | Count |
|---------------|-------|
| Critical      | 0     |
| High          | 0     |
| Medium        | 1     |
| Low           | 2     |
| Informational | 2     |

---

## Findings

### [M-01] Stale/fabricated OraclePack injection -- caller trust assumption

**Severity:** Medium
**Status:** Open
**Location:** `EMAGrowthTransformationLib.sol#L38-L67` -- `currentOraclePack` parameter

**Description:**
`currentOraclePack` is accepted as a value-type parameter (`OraclePack` is `uint256`). The function trusts it completely for:
1. The epoch comparison (line 46) -- a stale epoch causes the function to proceed when it should no-op, or to no-op when it should proceed.
2. The clamp anchor (line 60) -- `clampTick` uses `currentOraclePack.lastTick()`. A fabricated OraclePack with a manipulated `lastTick` shifts the clamp window, allowing an attacker to bypass clamping entirely.
3. The timeDelta computation (line 63) -- a wrong `epoch()` produces a wrong timeDelta, causing EMA over-convergence or under-convergence.

**Impact:**
If the caller is a permissionless external function (or if the caller reads OraclePack from user-supplied calldata rather than trusted storage), an attacker can:
- Feed a zero-epoch OraclePack to maximize timeDelta, causing all EMAs to converge ~75% toward the manipulated tick in one call.
- Set `lastTick` to any value to shift the clamp window to allow an arbitrary tick through.

**Mitigation:**
This is a caller-responsibility issue. The library itself is pure computation. However, the risk is real if any caller path exposes this parameter to user input. **Recommendation:** Add a NatSpec `@notice` warning that `currentOraclePack` MUST come from trusted storage, not user calldata. Verify all call sites enforce this.

**Verdict:** CONDITIONAL PASS -- safe if and only if all callers load OraclePack from storage.

---

### [L-01] clampDelta is caller-controlled with no upper bound validation

**Severity:** Low
**Status:** Open
**Location:** `EMAGrowthTransformationLib.sol#L41` -- `clampDelta` parameter

**Description:**
`clampDelta` is `int24`, range [-8388608, 8388607]. The BTT spec (Section 6.7) acknowledges that `clampDelta = type(int24).max` effectively disables clamping. A negative `clampDelta` is more concerning: in `OraclePackLibrary.clampTick` (line 511-528 of OraclePack.sol), the comparisons `_lastTick + clampDelta` and `_lastTick - clampDelta` with a negative `clampDelta` would invert the clamp bounds. Under `unchecked` arithmetic in `clampTick`, `_lastTick + negativeDelta` < `_lastTick - negativeDelta`, meaning `newTick` would almost always be outside the inverted range, and the function would clamp to `_lastTick + negativeDelta` (a tick BELOW lastTick) or `_lastTick - negativeDelta` (a tick ABOVE lastTick). This effectively inverts the direction of clamping.

**Impact:**
If a caller passes a negative `clampDelta`, the clamp logic produces counter-intuitive results. No fund loss directly, but oracle accuracy degrades.

**Recommendation:**
Either: (a) change parameter type to `uint24` and cast internally, or (b) add `require(clampDelta >= 0)`.

**Verdict:** PASS with caveat -- the library delegates validation to caller.

---

### [L-02] Epoch check before buffer check creates inconsistent revert behavior

**Severity:** Low
**Status:** Open
**Location:** `EMAGrowthTransformationLib.sol#L45-L50`

**Description:**
The epoch check (line 46) short-circuits before the buffer count check (line 49-50). If the buffer is empty but the epoch matches, the function returns successfully without reverting. If the epoch differs, it reverts with `InsufficientObservations`. This means the function's revert behavior depends on timing (which epoch you call in), not just on buffer state.

**Impact:**
No direct security impact. Could mask a misconfigured pool (empty buffer) that silently returns stale OraclePack data until the epoch advances, at which point it suddenly reverts.

**Recommendation:**
Consider checking `observationCount >= 2` before the epoch check, or document this as intentional (the BTT spec Section 2.1 calls this "gas optimization" for same-epoch path).

**Verdict:** PASS -- intentional per spec.

---

### [I-01] uint24 epoch arithmetic is safe for all realistic scenarios

**Severity:** Informational (audit question #2)
**Location:** `EMAGrowthTransformationLib.sol#L45,L63`

**Analysis:**
- `currentEpoch` = `uint24((block.timestamp >> 6) & 0xFFFFFF)` -- safe, always fits uint24.
- `uint24(currentEpoch - currentOraclePack.epoch())` on line 63: Solidity 0.8+ `uint24` subtraction would revert on underflow if `currentEpoch < recordedEpoch`. However, this line is reached only when `currentEpoch != recordedEpoch` (line 46 check). The question is: can `recordedEpoch > currentEpoch` after 24-bit wrap?

  **Yes, it can.** If `recordedEpoch = 0xFFFFFE` and `currentEpoch = 0x000001` (wrap occurred), then `currentEpoch - recordedEpoch` = `0x000001 - 0xFFFFFE` = underflow revert in checked arithmetic.

  **BUT:** The subtraction `uint24(currentEpoch - currentOraclePack.epoch())` is NOT inside an `unchecked` block. Solidity 0.8.26 checked arithmetic will revert on this underflow.

  **Wait** -- re-reading: `int256(uint256(uint24(currentEpoch - currentOraclePack.epoch())))`. The innermost cast is `uint24(currentEpoch - currentOraclePack.epoch())`. Both `currentEpoch` and `.epoch()` return `uint24`. The subtraction `currentEpoch - currentOraclePack.epoch()` happens in `uint24` arithmetic. In Solidity 0.8+, this REVERTS on underflow.

  **This is a bug at 24-bit wraparound.** After ~34.1 years, when the epoch counter wraps from 0xFFFFFF to 0x000000, any OraclePack with a pre-wrap epoch will cause a revert. The BTT spec (Section 6.5) claims the subtraction "wraps to 1 in unchecked arithmetic" but the code does NOT use `unchecked`.

**Verdict:** **BUG CONFIRMED** -- epoch wraparound causes permanent revert. Upgrading severity:

### [M-02] Epoch subtraction reverts on 24-bit wraparound (checked arithmetic)

**Severity:** Medium (becomes Critical only after ~34 years, but still a correctness bug)
**Status:** Open
**Location:** `EMAGrowthTransformationLib.sol#L63`

**Description:**
The subtraction `uint24(currentEpoch - currentOraclePack.epoch())` is in checked arithmetic context. When the 24-bit epoch counter wraps (after ~34.1 years), `currentEpoch < recordedEpoch` and the subtraction reverts with arithmetic underflow.

The BTT spec explicitly expects unchecked wraparound behavior (Section 6.5) but the code does not use `unchecked`.

**Fix:**
```solidity
int256 timeDelta;
unchecked {
    timeDelta = int256(uint256(uint24(currentEpoch - currentOraclePack.epoch()))) * 64;
}
```

**Verdict:** FAIL -- correctness bug. Low urgency (34-year horizon) but trivial fix.

---

### [I-02] View mutability, reentrancy, and gas griefing assessment

**Severity:** Informational (audit questions #6, #7, #8)

**View safety:** PASS. The function is `view`. All dependencies are pure arithmetic or storage reads (`CircularBuffer.last` uses SLOAD). No `extsload`, `delegatecall`, `staticcall` to external contracts, or hidden state changes anywhere in the call chain. `GrowthToTickLib.growthToTick` is `pure`. `OraclePackLibrary` functions are all `pure` or `internal pure`. Safe.

**Reentrancy:** PASS. Zero external calls. The `CircularBuffer.last()` reads from the contract's own storage via SLOAD. No callback vectors exist.

**Gas griefing:** PASS. The function performs exactly 2 SLOADs (oldest + latest observation) regardless of buffer state. `observationCount` is one additional SLOAD. The `insertObservation` loop is fixed at 8 iterations. `growthToTick` is bounded computation. No variable-length loops or unbounded operations. Maximum gas cost is deterministic and bounded (~50k gas worst case).

---

## Focused Analysis Results

| # | Question | Verdict | Notes |
|---|----------|---------|-------|
| 1 | Oracle manipulation via observation timing | PASS | Oldest/latest are deterministic from buffer state. Attacker cannot choose which observations are read. The keeper access control on `record()` prevents injection. The clamp mechanism limits per-epoch impact. |
| 2 | Epoch arithmetic overflow | **FAIL** | Checked arithmetic reverts on 24-bit wrap. See M-02. |
| 3 | timeDelta sign | PASS | `uint24(x - y)` where x != y and x > y (checked, reverts otherwise) always produces a positive uint24. Cast chain `int256(uint256(uint24(...)))` is always non-negative. `* 64` cannot overflow int256. OraclePack.updateEMAs uses timeDelta as positive seconds. |
| 4 | clampDelta bypass | **CONDITIONAL** | Negative clampDelta inverts clamp logic (see L-01). Max positive clampDelta disables clamping (by design per spec). Caller must validate. |
| 5 | Stale OraclePack injection | **CONDITIONAL** | See M-01. Safe if caller loads from storage. |
| 6 | View mutability | PASS | No hidden state changes. |
| 7 | Reentrancy | PASS | No external calls. |
| 8 | Gas griefing | PASS | Bounded, deterministic gas cost. |

---

## Overall Assessment

The library is well-structured, minimal, and correctly composes its dependencies. The two actionable findings are:

1. **M-02 (epoch wraparound):** Wrap the timeDelta computation in `unchecked`. Trivial fix, low urgency, but the code contradicts the spec.
2. **M-01 (stale OraclePack):** Document the trust requirement. Verify all call sites load from storage.

No Critical or High findings. The code is safe to deploy with the above fixes.
