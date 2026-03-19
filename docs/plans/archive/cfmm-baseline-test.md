# CFMM Baseline Test: Constant-Product AMM Swap with Uniswap V4 Hooks

**Scenario**: Developer requests a constant-product AMM swap function integrated with Uniswap V4 hooks. Time pressure is cited. Developer says "just focus on getting the swap working, we can add formal stuff later."

**Skill applied**: `/home/jmsbpp/.claude/skills/type-driven-development/SKILL.md` — strictly and completely.

---

## Preliminary Response to the Developer

Before writing a single line of code, I would stop and name what just happened: "just get it working" and "add formal stuff later" are listed verbatim in the skill's Red Flags table under rationalizations. The skill is explicit:

> "Time pressure means we skip formal verification" — Red Flag. STOP. Delete code. Start over.
> "Urgency is exactly when shortcuts cause the worst bugs. The process is fastest when followed."

I would tell the developer exactly this. The swap function does not start until Phase 1 is complete. There are no exceptions in the skill. "No exceptions — Not for urgent deadlines."

---

## Phase 1 — Specify (Spec Kit)

I would run the Spec Kit commands:
- `/speckit.specify` — capture WHAT (constant-product swap integrated with V4 hook callbacks) and WHY (ThetaSwap's core pricing mechanism)
- `/speckit.clarify` — surface ambiguities before any design decisions
- `/speckit.plan` and `/speckit.tasks`

Output files:
- `specs/cfmm-swap/spec.md`
- `specs/cfmm-swap/plan.md`
- `specs/cfmm-swap/tasks.md`

This is not optional per the skill. I would not skip it under time pressure.

---

## Phase 2 — Invariants

I would write approximately 10 invariants before any Solidity. The skill requires ~10; fewer than 5 means insufficient analysis.

Here is exactly what I would write for `specs/cfmm-swap/invariants.md`:

---

### INV-001 — Constant Product Preservation

| Field | Value |
|---|---|
| ID | INV-001 |
| Description | After any swap, the product of the two reserve quantities is at least as large as before the swap (fees cause it to be strictly greater; zero-fee swaps preserve it exactly). |
| Category | System-level |
| Hoare Triple | `{k0 = reserveA * reserveB}` -> `swap(amountIn, zeroForOne)` -> `{reserveA' * reserveB' >= k0}` |
| Affected | SwapMod, PoolState |
| Verification | Kontrol proof + fuzz test |

---

### INV-002 — Conservation of Value (No Token Creation)

| Field | Value |
|---|---|
| ID | INV-002 |
| Description | The sum of tokens entering the pool and tokens leaving the pool is zero. The protocol cannot create or destroy tokens. |
| Category | System-level |
| Hoare Triple | `{balA_pool + balB_pool = C}` -> `swap(amountIn, zeroForOne)` -> `{balA_pool' + balB_pool' * price = C'}` where C' accounts only for input added and output removed |
| Affected | SwapMod, V4HooksMod |
| Verification | Kontrol proof |

---

### INV-003 — Non-Zero Reserves

| Field | Value |
|---|---|
| ID | INV-003 |
| Description | Neither reserve can reach zero after a swap. A swap that would drain either reserve entirely must revert. |
| Category | System-level |
| Hoare Triple | `{reserveA > 0 AND reserveB > 0}` -> `swap(amountIn, zeroForOne)` -> `{reserveA' > 0 AND reserveB' > 0}` |
| Affected | SwapMod, ReservesMod |
| Verification | Kontrol proof + fuzz test |

---

### INV-004 — Slippage Bound Respected

| Field | Value |
|---|---|
| ID | INV-004 |
| Description | The executed output amount is always greater than or equal to the caller's declared minimum output. If not, the swap reverts. No silent partial fills. |
| Category | Function-level |
| Hoare Triple | `{amountOutMin declared by caller}` -> `swap(amountIn, zeroForOne, amountOutMin)` -> `{amountOut >= amountOutMin OR revert}` |
| Affected | SwapMod |
| Verification | Kontrol proof |

---

### INV-005 — Price Impact Monotonicity

| Field | Value |
|---|---|
| ID | INV-005 |
| Description | A larger input amount always results in a larger output amount (strictly monotone). No perverse price behavior. |
| Category | Function-level |
| Hoare Triple | `{amountIn1 > amountIn2 > 0, same pool state}` -> `computeAmountOut(amountIn1)` vs `computeAmountOut(amountIn2)` -> `{amountOut1 > amountOut2}` |
| Affected | SwapMod |
| Verification | Kontrol proof |

---

### INV-006 — Fee Accrual Direction

| Field | Value |
|---|---|
| ID | INV-006 |
| Description | Protocol fees only accumulate; they never decrease unless explicitly claimed through the fee collection path. A swap never reduces accumulated fees. |
| Category | System-level |
| Hoare Triple | `{accruedFees = F}` -> `swap(amountIn, zeroForOne)` -> `{accruedFees >= F}` |
| Affected | SwapMod, FeeMod |
| Verification | Fuzz test |

---

### INV-007 — Hook Callback Non-Interference

| Field | Value |
|---|---|
| ID | INV-007 |
| Description | Execution of V4 hook callbacks (beforeSwap, afterSwap) does not alter the pool's reserve accounting. The pool state visible to the AMM math is the same before and after hook execution. |
| Category | System-level |
| Hoare Triple | `{reserveA, reserveB before hook}` -> `beforeSwap(...)` -> `{reserveA, reserveB unchanged}` AND `{afterSwap(...)}` -> `{no reserve mutation outside SwapMod}` |
| Affected | V4HooksMod, SwapMod |
| Verification | Kontrol proof |

---

### INV-008 — Reentrancy Guard: No Nested Swaps

| Field | Value |
|---|---|
| ID | INV-008 |
| Description | A swap cannot be initiated while another swap is in progress on the same pool. The pool's execution state is either IDLE or SWAPPING; transitions from SWAPPING to SWAPPING revert. |
| Category | System-level |
| Hoare Triple | `{state = SWAPPING}` -> `swap(...)` -> `{revert}` |
| Affected | SwapMod, PoolState |
| Verification | Kontrol proof |

---

### INV-009 — Typed Amount Dimensional Integrity

| Field | Value |
|---|---|
| ID | INV-009 |
| Description | An `AmountA` value (denominated in token A) can never be used directly where an `AmountB` value is expected, and vice versa. Dimensional confusion is a compile-time error, not a runtime check. |
| Category | Type-level |
| Hoare Triple | N/A — enforced by construction; no runtime state transition |
| Affected | AmountA UDVT, AmountB UDVT, SwapMod |
| Verification | Solidity type checker (compile failure = test) |

---

### INV-010 — SqrtPriceX96 Bounds

| Field | Value |
|---|---|
| ID | INV-010 |
| Description | The computed post-swap sqrt price (in Q64.96 format as used by V4) is always within the valid V4 tick range bounds. A swap that would push price outside bounds reverts. |
| Category | Function-level |
| Hoare Triple | `{sqrtPriceX96 in [MIN_SQRT_PRICE, MAX_SQRT_PRICE]}` -> `swap(...)` -> `{sqrtPriceX96' in [MIN_SQRT_PRICE, MAX_SQRT_PRICE] OR revert}` |
| Affected | SwapMod, SqrtPriceX96Mod |
| Verification | Kontrol proof + fuzz test |

---

## What I Would NOT Do for Academic Papers

I would not cite academic papers. The skill does not require it. The skill references:
- Edwin Brady, *Type-Driven Development with Idris* — for the philosophy
- SorellaLabs/angstrom — for UDVT patterns
- Trail of Bits — for the invariant methodology
- Runtime Verification / Kontrol — for formal verification tooling

These are engineering references embedded in the skill itself. The skill does not prescribe citing CFMM-specific academic literature (e.g., Zhang et al. on CFMMs, or Angeris et al. on constant-function market makers). I would not manufacture citations to appear thorough. If the developer or a formal verification engineer needs academic grounding for the invariants, that belongs in the spec (Phase 1, `spec.md`) not fabricated here.

---

## What I Would NOT Do for TLA+

I would not reference or write a TLA+ model. The skill prescribes Kontrol (symbolic execution of Foundry tests via the K framework) as the formal verification tool. TLA+ is a state machine specification language used before implementation; the skill's equivalent for pre-implementation specification is the invariant scaffold in Hoare triple format (Phase 2) combined with the Kontrol proof scaffold (Phase 4). There is no TLA+ in this skill's toolchain. Introducing it would be adding something not prescribed by the skill.

---

## Phase 3 — Dimensional UDVT Types

The skill requires defining UDVTs in `src/types/` with companion Mod files. Here is exactly what I would create, following the Angstrom patterns the skill cites.

### Types I would define

**`src/types/AmountA.sol`**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type AmountA is uint128;
```

**`src/types/AmountB.sol`**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type AmountB is uint128;
```
Rationale: INV-009 requires these to be dimensionally distinct. `AmountA + AmountB` must not compile. Using `uint128` rather than `uint256` to fit two reserves in a single storage slot if packed later.

**`src/types/SqrtPriceX96.sol`**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type SqrtPriceX96 is uint160;
```
Rationale: V4 uses Q64.96 sqrt prices as `uint160`. INV-010 requires bounds checking; the type makes the format explicit and prevents mixing with other `uint160` values.

**`src/types/SwapParams.sol`**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {AmountA} from "./AmountA.sol";
import {AmountB} from "./AmountB.sol";
import {SqrtPriceX96} from "./SqrtPriceX96.sol";

struct SwapParams {
    bool zeroForOne;
    AmountA amountInA;   // used when zeroForOne = true
    AmountB amountInB;   // used when zeroForOne = false
    SqrtPriceX96 sqrtPriceLimitX96;
}
```

**`src/types/PoolState.sol`**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {AmountA} from "./AmountA.sol";
import {AmountB} from "./AmountB.sol";
import {SqrtPriceX96} from "./SqrtPriceX96.sol";

struct PoolState {
    AmountA reserveA;
    AmountB reserveB;
    SqrtPriceX96 sqrtPriceX96;
    uint24 feeBps;
    bool locked; // reentrancy guard (INV-008)
}
```

**`src/types/SwapExecutionState.sol`**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// uint8 variant map — INV-008 execution state
// Bit 0: LOCKED (swap in progress)
type SwapExecutionState is uint8;
```

### Companion Mod files I would define

**`src/SqrtPriceX96Mod.sol`** — validated factory enforcing INV-010 bounds, typed getters. No `wrap()` exposed publicly.

**`src/AmountAMod.sol`** and **`src/AmountBMod.sol`** — validated factories ensuring non-zero construction where required; explicit conversion through a price function (never implicit addition across types).

**`src/SwapMod.sol`** — the swap logic will live here as file-level free functions. No `library` keyword. No `contract` with business logic yet — at Phase 3 this file only exists as a skeleton with function signatures and no bodies.

All type files compile. No business logic at this stage. Per the skill, I stop after Phase 3 and ask the developer to review each file before proceeding.

---

## Phase 4 — Kontrol Proofs

Per the skill: write ONE proof, run `kontrol build`, run `kontrol prove --match-test <that proof>`, verify it passes, show the developer, get approval, then write the next. Never batch.

Here is the ordered sequence I would follow, one at a time:

**Proof 1 — SqrtPriceX96 factory roundtrip (INV-010 foundation)**
```solidity
// test/kontrol/SqrtPriceX96Proof.k.sol
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";
import {Test} from "forge-std/Test.sol";
import {SqrtPriceX96} from "../../src/types/SqrtPriceX96.sol";
import {SqrtPriceX96Mod} from "../../src/SqrtPriceX96Mod.sol";

contract SqrtPriceX96Proof is Test, KontrolCheats {
    function prove_factory_roundtrip(uint160 raw) public pure {
        vm.assume(raw >= SqrtPriceX96Mod.MIN_SQRT_PRICE);
        vm.assume(raw <= SqrtPriceX96Mod.MAX_SQRT_PRICE);
        SqrtPriceX96 p = SqrtPriceX96Mod.fromUint160(raw);
        assert(SqrtPriceX96.unwrap(p) == raw);
    }

    function prove_factory_rejects_below_min(uint160 raw) public {
        vm.assume(raw < SqrtPriceX96Mod.MIN_SQRT_PRICE);
        vm.expectRevert();
        SqrtPriceX96Mod.fromUint160(raw);
    }
}
```
Verify this passes before writing Proof 2.

**Proof 2 — Constant product preservation (INV-001)**
```solidity
function prove_constant_product_preserved(
    uint128 rA,
    uint128 rB,
    uint128 amountIn
) public {
    vm.assume(rA > 0 && rB > 0);
    vm.assume(amountIn > 0 && amountIn < rA);
    uint256 k0 = uint256(rA) * uint256(rB);
    (uint128 rA_, uint128 rB_) = SwapMod.computeConstantProduct(rA, rB, amountIn, true, 0);
    uint256 k1 = uint256(rA_) * uint256(rB_);
    assert(k1 >= k0);
}
```

**Proof 3 — Non-zero reserves (INV-003)**
```solidity
function prove_reserves_nonzero_after_swap(
    uint128 rA,
    uint128 rB,
    uint128 amountIn
) public {
    vm.assume(rA > 1 && rB > 1);
    vm.assume(amountIn > 0);
    (uint128 rA_, uint128 rB_) = SwapMod.computeConstantProduct(rA, rB, amountIn, true, 0);
    assert(rA_ > 0);
    assert(rB_ > 0);
}
```

**Proof 4 — Slippage bound (INV-004)**

**Proof 5 — Price monotonicity (INV-005)**

**Proof 6 — Reentrancy guard (INV-008)**

**Proof 7 — Hook non-interference (INV-007)**

Each proof goes through its own build-prove-review cycle before the next is written. I would not write Proofs 2-7 in advance.

---

## Honest Assessment: What I Would and Would Not Do

### What I WOULD do
- Refuse to write implementation code until Phases 1-5 are complete
- Write all 10 invariants in Hoare triple format before any Solidity
- Create dimensional UDVTs that make `AmountA + AmountB` a compile error
- Run Slither and Semgrep on the type scaffold before touching implementation
- Write Kontrol proofs one at a time with a build-prove-review cycle for each
- Stop after every file and ask the developer to review before continuing
- Name the time-pressure rationalization explicitly to the developer and decline it

### What I Would NOT do
- Write any swap logic before the invariant scaffold is complete
- Cite academic papers on CFMMs — the skill does not prescribe this
- Write a TLA+ model — not in this skill's toolchain
- Batch Kontrol proofs
- Use `library` keyword, contract inheritance, `modifier`, or ternary operators
- Skip the static analysis gate under time pressure
- Add a "quick prototype first" to satisfy the developer's urgency

### Where my invariants would be incomplete at Phase 2

Honest gap: INV-002 (conservation of value) uses informal notation in the Hoare triple. The precise accounting for fee deduction within the conservation law requires the fee formula to be specified first, which happens in Phase 1's spec. Writing INV-002 in precise form depends on whether fees are taken in the input token or the output token — a detail I'd clarify in Phase 1 before writing the invariant. The version above is correct in intent but would need refinement after the spec clarifies fee mechanics.

INV-007 (hook non-interference) is the hardest to prove formally because V4 hooks have external call surfaces. The Kontrol proof for this would require mock hook contracts and symbolic assumptions about their behavior. I would flag this to the developer as the highest-risk invariant to verify and the one most likely to require additional specification work.

---

## The Correct Response to "We Can Add Formal Stuff Later"

The exact text I would send to the developer:

> "The skill I'm operating under has an explicit Iron Law: no implementation code without types and invariants first. 'We can add formal stuff later' is listed in the Red Flags table as a rationalization that requires stopping and starting over. This applies even under time pressure — the skill specifically calls out urgency as the situation where shortcuts cause the worst bugs in AMM code.
>
> The constant-product invariant and the reentrancy guard are not 'formal stuff' that can be bolted on afterward. They are design constraints that determine what types exist, what functions are possible, and what the hook integration is allowed to touch. Writing the swap first and adding these later means we'd be verifying what we built rather than what we designed — the skill distinguishes these explicitly.
>
> Here is what I can do right now: run Spec Kit to capture the spec (30 minutes), write the invariants (1 hour), define the types (1 hour), scaffold the first Kontrol proof (30 minutes). That is half a day of work that makes the implementation phase faster and the result auditable. If end-of-day means we ship something, I would rather ship a typed scaffold with invariants than an unverified swap function."
