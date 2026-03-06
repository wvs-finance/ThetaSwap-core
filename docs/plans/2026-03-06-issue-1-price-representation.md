# Issue 1: Price Representation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the three foundational math types that map FCI oracle output (Delta+) to CFMM price primitives — enabling all downstream Issues 2-6.

**Architecture:** Three UDVT Mod files following existing codebase conventions (Q128 fixed-point, free functions, `using ... for ... global`). No storage, no hooks, no external calls. Pure math with Solady FixedPointMathLib for safe arithmetic.

**Tech Stack:** Solidity ^0.8.26, Solady FixedPointMathLib (mulDiv, sqrt), forge-std (Test, console2), Q128 = 1 << 128

**Reference patterns:**
- `src/fee-concentration-index/types/FeeShareRatioMod.sol` — Q128 UDVT + square() + mulDiv
- `src/fee-concentration-index/types/AccumulatedHHIMod.sol` — sqrt in Q128, capping
- `src/theta-swap-insurance/types/PremiumFactorMod.sol` — uint128 UDVT + applyTo

**LaTeX source of truth:**
- `specs/model/payoff.tex` §1.5: `p = Delta+ / (1 - Delta+)`, inverse `Delta+ = p / (1 + p)`
- `specs/model/trading-function.tex` §3.2: `u = x^2`, `x = sqrt(u)`
- `specs/model/trading-function.tex` §3.3: `p = (p_l^2 / 2) * sqrt(u / L_act)`
- `specs/model/reserves.tex` numerical table: p_l=0.0989, p_u=1.0

---

### Task 1: ConcentrationPriceMod — Type + Tests

**Files:**
- Create: `src/theta-swap-insurance/types/ConcentrationPriceMod.sol`
- Create: `test/theta-swap-insurance/unit/ConcentrationPrice.t.sol`

**Step 1: Write the failing test**

Create `test/theta-swap-insurance/unit/ConcentrationPrice.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    ConcentrationPrice,
    fromDeltaPlus,
    toDeltaPlus,
    unwrap as cpUnwrap,
    isZero as cpIsZero,
    gt as cpGt,
    Q128
} from "../../../src/theta-swap-insurance/types/ConcentrationPriceMod.sol";

contract ConcentrationPriceTest is Test {
    // --- fromDeltaPlus ---

    function test_fromDeltaPlus_zero() public pure {
        // Delta+ = 0 => p = 0/(1-0) = 0
        ConcentrationPrice p = fromDeltaPlus(0);
        assertEq(cpUnwrap(p), 0);
    }

    function test_fromDeltaPlus_half() public pure {
        // Delta+ = 0.5 (= Q128/2) => p = 0.5/0.5 = 1.0 (= Q128)
        uint256 halfQ128 = Q128 / 2;
        ConcentrationPrice p = fromDeltaPlus(halfQ128);
        // p should be Q128 (= 1.0)
        assertApproxEqRel(cpUnwrap(p), Q128, 1e12); // 0.0001% tolerance
    }

    function test_fromDeltaPlus_pointNine() public pure {
        // Delta+ = 0.09 => p = 0.09/0.91 = 0.09890109...
        // matches p_l = 0.0989 from reserves.tex numerical table
        uint256 d = (Q128 * 9) / 100; // 0.09 in Q128
        ConcentrationPrice p = fromDeltaPlus(d);
        // expected: 0.0989010989... * Q128
        uint256 expected = (Q128 * 9) / 91; // 9/91 = 0.098901...
        assertApproxEqRel(cpUnwrap(p), expected, 1e14); // 0.01% tolerance
    }

    function test_fromDeltaPlus_reverts_at_one() public {
        // Delta+ = Q128 (= 1.0) => denominator = 0, should revert
        vm.expectRevert();
        fromDeltaPlus(Q128);
    }

    // --- toDeltaPlus (inverse) ---

    function test_toDeltaPlus_zero() public pure {
        // p = 0 => Delta+ = 0/(1+0) = 0
        ConcentrationPrice p = ConcentrationPrice.wrap(0);
        assertEq(toDeltaPlus(p), 0);
    }

    function test_toDeltaPlus_one() public pure {
        // p = 1.0 (Q128) => Delta+ = 1/2 = Q128/2
        ConcentrationPrice p = ConcentrationPrice.wrap(Q128);
        assertApproxEqRel(toDeltaPlus(p), Q128 / 2, 1e12);
    }

    // --- Round-trip ---

    function test_roundTrip_fromDeltaPlus_toDeltaPlus() public pure {
        uint256 d = (Q128 * 33) / 100; // Delta+ = 0.33
        ConcentrationPrice p = fromDeltaPlus(d);
        uint256 recovered = toDeltaPlus(p);
        assertApproxEqRel(recovered, d, 1e12);
    }

    // --- Monotonicity ---

    function test_monotonicity() public pure {
        uint256 d1 = (Q128 * 10) / 100; // 0.10
        uint256 d2 = (Q128 * 20) / 100; // 0.20
        ConcentrationPrice p1 = fromDeltaPlus(d1);
        ConcentrationPrice p2 = fromDeltaPlus(d2);
        assertTrue(cpGt(p2, p1));
    }

    // --- isZero ---

    function test_isZero_true() public pure {
        assertTrue(cpIsZero(ConcentrationPrice.wrap(0)));
    }

    function test_isZero_false() public pure {
        assertFalse(cpIsZero(ConcentrationPrice.wrap(1)));
    }

    // --- Fuzz: round-trip ---

    function testFuzz_roundTrip(uint256 d) public pure {
        // Bound Delta+ to [0, Q128 - 1) to avoid division by zero
        d = bound(d, 0, Q128 - 2);
        ConcentrationPrice p = fromDeltaPlus(d);
        uint256 recovered = toDeltaPlus(p);
        if (d == 0) {
            assertEq(recovered, 0);
        } else {
            // Allow 1 wei rounding
            assertApproxEqAbs(recovered, d, 1);
        }
    }

    // --- Fuzz: monotonicity ---

    function testFuzz_monotonicity(uint256 d1, uint256 d2) public pure {
        d1 = bound(d1, 0, Q128 / 2 - 1);
        d2 = bound(d2, d1 + 1, Q128 - 2);
        ConcentrationPrice p1 = fromDeltaPlus(d1);
        ConcentrationPrice p2 = fromDeltaPlus(d2);
        assertTrue(cpUnwrap(p2) > cpUnwrap(p1));
    }
}
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-contract ConcentrationPriceTest -v 2>&1 | head -20`
Expected: Compilation error — `ConcentrationPriceMod.sol` does not exist yet.

**Step 3: Write minimal implementation**

Create `src/theta-swap-insurance/types/ConcentrationPriceMod.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

// Concentration price p = Delta+ / (1 - Delta+), in Q128 fixed-point.
// p in [0, inf) for Delta+ in [0, 1). Monotone increasing (FCI-10).
// Inverse: Delta+ = p / (1 + p).
// Source: specs/model/payoff.tex Definition 1.5

type ConcentrationPrice is uint256;

uint256 constant Q128 = 1 << 128;

error ConcentrationPrice__DeltaPlusAtOne();

function fromDeltaPlus(uint256 deltaPlusQ128) pure returns (ConcentrationPrice) {
    if (deltaPlusQ128 >= Q128) revert ConcentrationPrice__DeltaPlusAtOne();
    if (deltaPlusQ128 == 0) return ConcentrationPrice.wrap(0);
    // p = d / (Q128 - d), scaled to Q128: p_Q128 = d * Q128 / (Q128 - d)
    uint256 denom = Q128 - deltaPlusQ128;
    return ConcentrationPrice.wrap(FixedPointMathLib.mulDiv(deltaPlusQ128, Q128, denom));
}

function toDeltaPlus(ConcentrationPrice p) pure returns (uint256) {
    uint256 raw = ConcentrationPrice.unwrap(p);
    if (raw == 0) return 0;
    // Delta+ = p / (1 + p) = p / (Q128 + p) * Q128
    return FixedPointMathLib.mulDiv(raw, Q128, raw + Q128);
}

function unwrap(ConcentrationPrice p) pure returns (uint256) {
    return ConcentrationPrice.unwrap(p);
}

function isZero(ConcentrationPrice p) pure returns (bool) {
    return ConcentrationPrice.unwrap(p) == 0;
}

function gt(ConcentrationPrice a, ConcentrationPrice b) pure returns (bool) {
    return ConcentrationPrice.unwrap(a) > ConcentrationPrice.unwrap(b);
}

function lt(ConcentrationPrice a, ConcentrationPrice b) pure returns (bool) {
    return ConcentrationPrice.unwrap(a) < ConcentrationPrice.unwrap(b);
}

using {unwrap, isZero, gt, lt} for ConcentrationPrice global;
```

**Step 4: Run tests to verify they pass**

Run: `forge test --match-contract ConcentrationPriceTest -v`
Expected: All 11 tests pass (including 2 fuzz tests with 256 runs each).

**Step 5: Commit**

```bash
git add src/theta-swap-insurance/types/ConcentrationPriceMod.sol test/theta-swap-insurance/unit/ConcentrationPrice.t.sol
git commit -m "feat(types): add ConcentrationPriceMod — Delta+ to price odds ratio (FCI-09, FCI-10, FCI-11)"
```

---

### Task 2: TransformedReserveMod — Type + Tests

**Files:**
- Create: `src/theta-swap-insurance/types/TransformedReserveMod.sol`
- Create: `test/theta-swap-insurance/unit/TransformedReserve.t.sol`

**Step 1: Write the failing test**

Create `test/theta-swap-insurance/unit/TransformedReserve.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    TransformedReserve,
    fromX,
    toX,
    add as trAdd,
    sub as trSub,
    unwrap as trUnwrap,
    Q128
} from "../../../src/theta-swap-insurance/types/TransformedReserveMod.sol";

contract TransformedReserveTest is Test {
    // --- fromX ---

    function test_fromX_zero() public pure {
        TransformedReserve u = fromX(0);
        assertEq(trUnwrap(u), 0);
    }

    function test_fromX_one() public pure {
        // x = 1.0 (Q128) => u = x^2 = 1.0 (Q128)
        TransformedReserve u = fromX(Q128);
        assertApproxEqRel(trUnwrap(u), Q128, 1e12);
    }

    function test_fromX_two() public pure {
        // x = 2.0 (2*Q128) => u = 4.0 (4*Q128)
        TransformedReserve u = fromX(2 * Q128);
        assertApproxEqRel(trUnwrap(u), 4 * Q128, 1e12);
    }

    // --- toX ---

    function test_toX_zero() public pure {
        TransformedReserve u = TransformedReserve.wrap(0);
        assertEq(toX(u), 0);
    }

    function test_toX_one() public pure {
        // u = 1.0 (Q128) => x = sqrt(1.0) = 1.0 (Q128)
        TransformedReserve u = TransformedReserve.wrap(Q128);
        assertApproxEqRel(toX(u), Q128, 1e12);
    }

    function test_toX_four() public pure {
        // u = 4.0 (4*Q128) => x = sqrt(4.0) = 2.0 (2*Q128)
        TransformedReserve u = TransformedReserve.wrap(4 * Q128);
        assertApproxEqRel(toX(u), 2 * Q128, 1e12);
    }

    // --- Round-trip ---

    function test_roundTrip_fromX_toX() public pure {
        uint256 x = (Q128 * 314) / 100; // x = 3.14
        TransformedReserve u = fromX(x);
        uint256 recovered = toX(u);
        assertApproxEqRel(recovered, x, 1e12);
    }

    // --- add / sub ---

    function test_add() public pure {
        TransformedReserve a = TransformedReserve.wrap(Q128);
        TransformedReserve b = TransformedReserve.wrap(Q128 / 2);
        TransformedReserve c = trAdd(a, b);
        assertEq(trUnwrap(c), Q128 + Q128 / 2);
    }

    function test_sub() public pure {
        TransformedReserve a = TransformedReserve.wrap(Q128);
        TransformedReserve b = TransformedReserve.wrap(Q128 / 2);
        TransformedReserve c = trSub(a, b);
        assertEq(trUnwrap(c), Q128 / 2);
    }

    // --- Fuzz: round-trip ---

    function testFuzz_roundTrip(uint256 x) public pure {
        // Bound x to avoid overflow in x*x/Q128.
        // x^2 / Q128 must fit in uint256: x < sqrt(type(uint256).max * Q128)
        // Conservatively: x < 2^192 (since Q128 = 2^128, x^2/Q128 < 2^256 when x < 2^192)
        x = bound(x, 0, 1 << 192);
        TransformedReserve u = fromX(x);
        uint256 recovered = toX(u);
        if (x == 0) {
            assertEq(recovered, 0);
        } else {
            // sqrt introduces rounding; allow 1 part in 10^12
            assertApproxEqRel(recovered, x, 1e6); // 10^-12 relative
        }
    }

    // --- Fuzz: monotonicity ---

    function testFuzz_monotonicity(uint256 x1, uint256 x2) public pure {
        x1 = bound(x1, 0, (1 << 192) - 2);
        x2 = bound(x2, x1 + 1, 1 << 192);
        TransformedReserve u1 = fromX(x1);
        TransformedReserve u2 = fromX(x2);
        assertTrue(trUnwrap(u2) > trUnwrap(u1));
    }
}
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-contract TransformedReserveTest -v 2>&1 | head -20`
Expected: Compilation error — `TransformedReserveMod.sol` does not exist yet.

**Step 3: Write minimal implementation**

Create `src/theta-swap-insurance/types/TransformedReserveMod.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

// Transformed risky reserve: u = x^2, where x is the virtual concentration reserve.
// The coordinate transform u = x^2 makes the trading function psi(u,y) = y - (p_l^2/4)*u
// LINEAR in (u, y), enabling O(1) tick-based liquidity aggregation.
// Source: specs/model/trading-function.tex Definition 3.2 (CFMM-16)

type TransformedReserve is uint256;

uint256 constant Q128 = 1 << 128;

function fromX(uint256 xQ128) pure returns (TransformedReserve) {
    if (xQ128 == 0) return TransformedReserve.wrap(0);
    // u = x^2 in Q128: (x * x) / Q128
    return TransformedReserve.wrap(FixedPointMathLib.mulDiv(xQ128, xQ128, Q128));
}

function toX(TransformedReserve u) pure returns (uint256) {
    uint256 raw = TransformedReserve.unwrap(u);
    if (raw == 0) return 0;
    // x = sqrt(u) in Q128: sqrt(u * Q128)
    return FixedPointMathLib.sqrt(raw * Q128);
}

function add(TransformedReserve a, TransformedReserve b) pure returns (TransformedReserve) {
    return TransformedReserve.wrap(TransformedReserve.unwrap(a) + TransformedReserve.unwrap(b));
}

function sub(TransformedReserve a, TransformedReserve b) pure returns (TransformedReserve) {
    return TransformedReserve.wrap(TransformedReserve.unwrap(a) - TransformedReserve.unwrap(b));
}

function unwrap(TransformedReserve u) pure returns (uint256) {
    return TransformedReserve.unwrap(u);
}

using {toX, add, sub, unwrap} for TransformedReserve global;
```

**Step 4: Run tests to verify they pass**

Run: `forge test --match-contract TransformedReserveTest -v`
Expected: All 10 tests pass.

**Step 5: Commit**

```bash
git add src/theta-swap-insurance/types/TransformedReserveMod.sol test/theta-swap-insurance/unit/TransformedReserve.t.sol
git commit -m "feat(types): add TransformedReserveMod — u=x^2 coordinate transform (CFMM-16)"
```

---

### Task 3: SpotPriceMod — Type + Tests

**Files:**
- Create: `src/theta-swap-insurance/types/SpotPriceMod.sol`
- Create: `test/theta-swap-insurance/unit/SpotPrice.t.sol`

**Step 1: Write the failing test**

Create `test/theta-swap-insurance/unit/SpotPrice.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    SpotPrice,
    fromReserves,
    unwrap as spUnwrap,
    Q128
} from "../../../src/theta-swap-insurance/types/SpotPriceMod.sol";
import {
    TransformedReserve,
    fromX
} from "../../../src/theta-swap-insurance/types/TransformedReserveMod.sol";
import {
    ConcentrationPrice,
    fromDeltaPlus
} from "../../../src/theta-swap-insurance/types/ConcentrationPriceMod.sol";

contract SpotPriceTest is Test {
    // p_l = 0.0989 from reserves.tex numerical table (Delta* = 0.09)
    // p_l in Q128 = 0.0989 * Q128
    uint256 P_L_Q128 = (Q128 * 989) / 10000;

    // --- fromReserves basic ---

    function test_fromReserves_at_pL() public view {
        // At p = p_l: x = 2/p_l, u = x^2 = 4/p_l^2, L = 1 (Q128)
        // p = (p_l^2 / 2) * sqrt(u / L)
        //   = (p_l^2 / 2) * sqrt(4/p_l^2)
        //   = (p_l^2 / 2) * (2/p_l)
        //   = p_l
        // x = 2/p_l in Q128
        uint256 xQ128 = FixedPointMathLib.mulDiv(2 * Q128, Q128, P_L_Q128);
        TransformedReserve u = fromX(xQ128);
        uint256 L_act = Q128; // L = 1.0
        SpotPrice p = fromReserves(u, L_act, ConcentrationPrice.wrap(P_L_Q128));
        assertApproxEqRel(spUnwrap(p), P_L_Q128, 1e14); // 0.01% tolerance
    }

    function test_fromReserves_zero_u() public pure {
        // u = 0 => p = 0
        TransformedReserve u = TransformedReserve.wrap(0);
        SpotPrice p = fromReserves(u, Q128, ConcentrationPrice.wrap(Q128 / 10));
        assertEq(spUnwrap(p), 0);
    }

    function test_fromReserves_reverts_zero_liquidity() public {
        TransformedReserve u = TransformedReserve.wrap(Q128);
        vm.expectRevert();
        fromReserves(u, 0, ConcentrationPrice.wrap(Q128 / 10));
    }

    // --- Numerical verification against reserves.tex ---

    function test_numerical_reserves_table() public view {
        // From reserves.tex: at p = 0.5, x = 102.2 (per unit L at p_l=0.0989)
        // x(p) = 2p/p_l^2. At p=0.5: x = 2*0.5/0.0989^2 = 1.0/0.009781 = 102.24
        uint256 p_half = Q128 / 2; // p = 0.5
        // x = 2*p / p_l^2 = 2 * 0.5 / 0.0989^2
        uint256 plSquared = FixedPointMathLib.mulDiv(P_L_Q128, P_L_Q128, Q128);
        uint256 xQ128 = FixedPointMathLib.mulDiv(2 * p_half, Q128, plSquared);
        TransformedReserve u = fromX(xQ128);
        SpotPrice p = fromReserves(u, Q128, ConcentrationPrice.wrap(P_L_Q128));
        // Should recover p = 0.5
        assertApproxEqRel(spUnwrap(p), p_half, 1e14);
    }

    // --- Fuzz: monotonicity in u ---

    function testFuzz_monotoneInU(uint256 u1Raw, uint256 u2Raw) public pure {
        u1Raw = bound(u1Raw, 1, Q128 * 100);
        u2Raw = bound(u2Raw, u1Raw + 1, Q128 * 100 + 1);
        TransformedReserve u1 = TransformedReserve.wrap(u1Raw);
        TransformedReserve u2 = TransformedReserve.wrap(u2Raw);
        ConcentrationPrice pL = ConcentrationPrice.wrap(Q128 / 10); // p_l = 0.1
        SpotPrice p1 = fromReserves(u1, Q128, pL);
        SpotPrice p2 = fromReserves(u2, Q128, pL);
        assertTrue(spUnwrap(p2) >= spUnwrap(p1));
    }
}

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-contract SpotPriceTest -v 2>&1 | head -20`
Expected: Compilation error — `SpotPriceMod.sol` does not exist yet.

**Step 3: Write minimal implementation**

Create `src/theta-swap-insurance/types/SpotPriceMod.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {TransformedReserve} from "./TransformedReserveMod.sol";
import {ConcentrationPrice} from "./ConcentrationPriceMod.sol";

// Spot price derived from virtual reserves:
//   p = (p_l^2 / 2) * sqrt(u / L_act)
// where u is the transformed reserve and L_act is active liquidity.
// Source: specs/model/trading-function.tex Definition 3.3 (CFMM-06)

type SpotPrice is uint256;

uint256 constant Q128 = 1 << 128;

error SpotPrice__ZeroLiquidity();

function fromReserves(
    TransformedReserve u,
    uint256 L_actQ128,
    ConcentrationPrice p_l
) pure returns (SpotPrice) {
    uint256 uRaw = TransformedReserve.unwrap(u);
    if (uRaw == 0) return SpotPrice.wrap(0);
    if (L_actQ128 == 0) revert SpotPrice__ZeroLiquidity();

    uint256 plRaw = ConcentrationPrice.unwrap(p_l);

    // p_l^2 in Q128
    uint256 plSquaredQ128 = FixedPointMathLib.mulDiv(plRaw, plRaw, Q128);

    // sqrt(u / L_act) in Q128: sqrt(u * Q128 / L_act)
    uint256 sqrtUoverL = FixedPointMathLib.sqrt(FixedPointMathLib.mulDiv(uRaw, Q128, L_actQ128) * Q128);

    // p = (p_l^2 / 2) * sqrt(u/L) = plSquared * sqrtUoverL / (2 * Q128)
    uint256 p = FixedPointMathLib.mulDiv(plSquaredQ128, sqrtUoverL, 2 * Q128);

    return SpotPrice.wrap(p);
}

function unwrap(SpotPrice p) pure returns (uint256) {
    return SpotPrice.unwrap(p);
}

function isZero(SpotPrice p) pure returns (bool) {
    return SpotPrice.unwrap(p) == 0;
}

using {unwrap, isZero} for SpotPrice global;
```

**Step 4: Run tests to verify they pass**

Run: `forge test --match-contract SpotPriceTest -v`
Expected: All 5 tests pass (including 1 fuzz test).

**Step 5: Commit**

```bash
git add src/theta-swap-insurance/types/SpotPriceMod.sol test/theta-swap-insurance/unit/SpotPrice.t.sol
git commit -m "feat(types): add SpotPriceMod — spot price from reserves p=(p_l^2/2)*sqrt(u/L) (CFMM-06)"
```

---

### Task 4: Cross-Type Integration Test

**Files:**
- Create: `test/theta-swap-insurance/unit/PriceRepresentation.t.sol`

**Step 1: Write the integration test**

This test verifies the full pipeline: Delta+ → p → reserves → spot price → recovered p.

Create `test/theta-swap-insurance/unit/PriceRepresentation.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

import {
    ConcentrationPrice,
    fromDeltaPlus,
    toDeltaPlus,
    Q128
} from "../../../src/theta-swap-insurance/types/ConcentrationPriceMod.sol";
import {
    TransformedReserve,
    fromX
} from "../../../src/theta-swap-insurance/types/TransformedReserveMod.sol";
import {
    SpotPrice,
    fromReserves
} from "../../../src/theta-swap-insurance/types/SpotPriceMod.sol";

contract PriceRepresentationIntegrationTest is Test {
    // Numerical verification of the full pipeline against reserves.tex table.
    // Parameters: p_l = 0.0989 (Delta* = 0.09), p_u = 1.0, L = 1.0

    uint256 constant P_L = (Q128 * 989) / 10000; // 0.0989
    uint256 constant P_U = Q128;                   // 1.0

    // --- Full pipeline: Delta+ -> p -> x(p) -> u=x^2 -> spotPrice -> compare ---

    function test_pipeline_at_deltaStar() public view {
        // Delta+ = 0.09 => p = 0.09/0.91 = 0.0989...
        uint256 deltaPlus = (Q128 * 9) / 100;
        ConcentrationPrice p = fromDeltaPlus(deltaPlus);

        // x(p) = 2p / p_l^2 (per unit L)
        uint256 plSquared = FixedPointMathLib.mulDiv(P_L, P_L, Q128);
        uint256 pRaw = ConcentrationPrice.unwrap(p);
        uint256 xQ128 = FixedPointMathLib.mulDiv(2 * pRaw, Q128, plSquared);

        // u = x^2
        TransformedReserve u = fromX(xQ128);

        // Spot price from reserves (L = 1.0 = Q128)
        SpotPrice pSpot = fromReserves(u, Q128, ConcentrationPrice.wrap(P_L));

        // Should recover original p (within rounding)
        assertApproxEqRel(SpotPrice.unwrap(pSpot), pRaw, 1e13); // 0.001%
    }

    function test_pipeline_at_half() public view {
        // Delta+ = 0.333... => p = 0.5
        uint256 deltaPlus = (Q128 * 333) / 1000;
        ConcentrationPrice p = fromDeltaPlus(deltaPlus);

        uint256 plSquared = FixedPointMathLib.mulDiv(P_L, P_L, Q128);
        uint256 pRaw = ConcentrationPrice.unwrap(p);
        uint256 xQ128 = FixedPointMathLib.mulDiv(2 * pRaw, Q128, plSquared);
        TransformedReserve u = fromX(xQ128);
        SpotPrice pSpot = fromReserves(u, Q128, ConcentrationPrice.wrap(P_L));

        assertApproxEqRel(SpotPrice.unwrap(pSpot), pRaw, 1e13);
    }

    function test_pipeline_at_pU() public view {
        // Delta+ = 0.5 => p = 1.0 = p_u
        uint256 deltaPlus = Q128 / 2;
        ConcentrationPrice p = fromDeltaPlus(deltaPlus);
        uint256 pRaw = ConcentrationPrice.unwrap(p);

        // At p = p_u: x = 2*p_u/p_l^2
        uint256 plSquared = FixedPointMathLib.mulDiv(P_L, P_L, Q128);
        uint256 xQ128 = FixedPointMathLib.mulDiv(2 * pRaw, Q128, plSquared);
        TransformedReserve u = fromX(xQ128);
        SpotPrice pSpot = fromReserves(u, Q128, ConcentrationPrice.wrap(P_L));

        assertApproxEqRel(SpotPrice.unwrap(pSpot), pRaw, 1e13);
    }

    // --- Collateral value check from reserves.tex ---

    function test_collateral_value_at_pL() public view {
        // V(p_l) = (p_u^2 - p_l^2) / p_l^2
        // = (1.0 - 0.0989^2) / 0.0989^2
        // = (1.0 - 0.009781) / 0.009781
        // = 101.2 (matches reserves.tex table)
        uint256 plSquared = FixedPointMathLib.mulDiv(P_L, P_L, Q128);
        uint256 puSquared = FixedPointMathLib.mulDiv(P_U, P_U, Q128);
        uint256 V = FixedPointMathLib.mulDiv(puSquared - plSquared, Q128, plSquared);
        // V should be approximately 101.2 * Q128
        uint256 expected = (Q128 * 1012) / 10;
        assertApproxEqRel(V, expected, 5e15); // 0.5% tolerance (rounding)
    }

    // --- Fuzz: full pipeline round-trip ---

    function testFuzz_pipelineRoundTrip(uint256 deltaPlus) public view {
        // Bound to avoid overflow: keep prices manageable
        deltaPlus = bound(deltaPlus, Q128 / 1000, Q128 / 2); // [0.001, 0.5]

        ConcentrationPrice p = fromDeltaPlus(deltaPlus);
        uint256 pRaw = ConcentrationPrice.unwrap(p);

        // Compute x(p) = 2p / p_l^2
        uint256 plSquared = FixedPointMathLib.mulDiv(P_L, P_L, Q128);
        uint256 xQ128 = FixedPointMathLib.mulDiv(2 * pRaw, Q128, plSquared);

        // Guard against overflow: x must be < 2^192 for fromX
        if (xQ128 > uint256(1) << 192) return;

        TransformedReserve u = fromX(xQ128);
        SpotPrice pSpot = fromReserves(u, Q128, ConcentrationPrice.wrap(P_L));

        // Round-trip tolerance: 0.01% (multiple sqrt + mulDiv operations)
        assertApproxEqRel(SpotPrice.unwrap(pSpot), pRaw, 1e14);
    }
}
```

**Step 2: Run integration test**

Run: `forge test --match-contract PriceRepresentationIntegrationTest -v`
Expected: All 5 tests pass.

**Step 3: Commit**

```bash
git add test/theta-swap-insurance/unit/PriceRepresentation.t.sol
git commit -m "test(types): add cross-type integration test for price representation pipeline"
```

---

### Task 5: Verify full build + run all Issue 1 tests

**Step 1: Run all Issue 1 tests together**

Run: `forge test --match-path "test/theta-swap-insurance/unit/*Price*" --match-path "test/theta-swap-insurance/unit/*Reserve*" -v`

Or more broadly: `forge test --match-path "test/theta-swap-insurance/unit/" -v`

Expected: All tests from Tasks 1-4 pass.

**Step 2: Verify no regressions**

Run: `forge test --skip "liquidity-supply-model" --skip "InsurancePoolMod" -v 2>&1 | tail -5`

Expected: All existing tests still pass.

**Step 3: Final commit with issue reference**

```bash
git add -A && git commit -m "feat(issue-1): complete Price Representation — ConcentrationPrice, TransformedReserve, SpotPrice

All 3 foundational types for the power² CFMM:
- ConcentrationPrice: Delta+/(1-Delta+) odds ratio (FCI-09, FCI-10, FCI-11)
- TransformedReserve: u=x² coordinate transform (CFMM-16)
- SpotPrice: p=(p_l²/2)·sqrt(u/L) from reserves (CFMM-06)

Full pipeline verified against reserves.tex numerical table."
```
