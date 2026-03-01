# Type-Driven Development Skill — Design Document

**Date:** 2026-03-01
**Status:** Approved

## Core Principle

Define types and invariants BEFORE writing any implementation. Types encode domain rules at compile time; invariants verify them at runtime and formally. If the types are right, the code writes itself. If the invariants pass, the code is correct.

## Process: 7 Phases

```
SPECIFY → INVARIANTS → TYPES → PROOFS → STATIC ANALYSIS → IMPLEMENT → VERIFY
```

### Phase 1 — Specify (Spec Kit required)

- `/speckit.specify` — capture WHAT and WHY
- `/speckit.clarify` — resolve ambiguities
- `/speckit.plan` — tech stack and architecture
- `/speckit.tasks` — actionable breakdown
- Output: `specs/<feature>/spec.md`, `plan.md`, `tasks.md`

### Phase 2 — Define Invariants

- Write ~10 system invariants before any code
- Format: Hoare triples (precondition -> action -> postcondition)
- Categorize: function-level (pure/view) vs system-level (state transitions) vs type-level (enforced by construction)
- Output: `specs/<feature>/invariants.md`

Each invariant gets:

| Field | Example |
|---|---|
| ID | INV-001 |
| Description | Total supply equals sum of all balances |
| Category | System-level |
| Hoare Triple | {totalSupply == sum(balances)} -> transfer(from, to, amt) -> {totalSupply == sum(balances)} |
| Affected | FeeRevenueInfo, LiquidityMetrics |
| Verification | Kontrol proof + fuzz test |

Rule of ~10: fewer than 5 means insufficient analysis, more than 20 means mixing invariants with test cases.

### Phase 3 — Design Types

- Define UDVTs, structs, enums in `src/types/`
- Write companion file-level free functions (Mod files) with `using ... for ... global`
- SCOP rules: no inheritance, no `library` keyword, no imports in contract files, file-level free functions for helpers
- Types must compile but no business logic yet
- Each file reviewed by user before moving to next

#### Type Patterns

**Pattern 1 — Dimensional Types (prevent unit confusion)**

```solidity
type AmountA is uint256;
type AmountB is uint256;
type PriceAB is uint256;

using {addA as +, subA as -} for AmountA global;
using {addB as +, subB as -} for AmountB global;
```

Conversion only through explicit price functions. Compiler rejects `AmountA + AmountB`.

**Pattern 2 — Opaque Construction (invariants at the boundary)**

```solidity
function init(uint16 spacing, uint24 fee) internal pure returns (ValidatedConfig) {
    if (spacing < MIN) revert InvalidSpacing();
    if (fee > MAX_FEE) revert FeeAboveMax();
    return ValidatedConfig.wrap(...);
}
```

No public `wrap()`. If you have a `ValidatedConfig`, it's valid.

**Pattern 3 — Bit-Packed Layouts with Typed Accessors**

```solidity
type FeeRevenueInfo is uint256;
// bits 0-47: startBlock, 48-95: commitment, 96-175: feeRevenue0, 176-255: feeRevenue1
// All access through library getters/setters with assembly
```

**Pattern 4 — Typed Zero as Sentinel**

No separate boolean flags. Zero value of the type encodes absence.

**Pattern 5 — Variant Maps (typed bitmask enums)**

```solidity
type SwapVariantMap is uint8;
// Each bit is a named flag with named accessor predicates
// Compiler prevents passing SwapVariantMap where OrderVariantMap expected
```

**Pattern 6 — File-Level Free Functions as Modules (SCOP)**

```solidity
// FeeRevenueMod.sol — NOT a library, NOT a contract
function getStorage() pure returns (FeeStorage storage s) {
    bytes32 position = keccak256("thetaswap.feerevenue");
    assembly { s.slot := position }
}
```

**The Idris principle:** Make invalid states unrepresentable. If two values shouldn't be added, make them different types. If a field has a range constraint, enforce it in the only factory function. If a value can be absent, encode absence as the zero value of the type.

### Phase 4 — Scaffold Kontrol Proofs

- Write ONE proof at a time
- Each proof expressed as a Foundry test with `prove_` prefix
- Use `KontrolCheats` + `vm.setArbitraryStorage` for symbolic execution
- Workflow per proof: write -> `kontrol build` -> `kontrol prove --match-test <proof>` -> verify -> user review -> next proof
- Output: `test/kontrol/<Feature>.k.sol` files

```solidity
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";

contract FeeRevenueProof is Test, KontrolCheats {
    function prove_feeRevenue_packUnpack(
        uint48 startBlock, uint48 commitment, uint80 fee0, uint80 fee1
    ) public {
        FeeRevenueInfo info = FeeRevenueInfoLibrary.init(startBlock, commitment, fee0, fee1);
        assert(info.startBlock() == startBlock);
        assert(info.commitment() == commitment);
        assert(info.feeRevenue0() == fee0);
        assert(info.feeRevenue1() == fee1);
    }
}
```

Naming: `prove_` for Kontrol, `test_` for unit tests, `testFuzz_` for fuzz tests.

### Phase 5 — Static Analysis Gate

Before implementation (on type scaffold):

- Slither: `slither src/ --filter-paths "test/"`
- Semgrep with Decurity smart contract rules: `semgrep --config https://github.com/Decurity/semgrep-smart-contracts --metrics=off src/`
- Fix all findings before proceeding

After implementation, run both again on full codebase.

### Phase 6 — Implement

- Write logic inside the typed scaffold
- SCOP style: file-level free functions for helpers, explicit enter()/exit() for reentrancy, inline auth checks
- Types constrain what you can write — if something doesn't typecheck, the design is wrong, not the code
- Each file reviewed by user before moving to next

### Phase 7 — Verify

- `kontrol prove` — all formal proofs pass
- `forge test` — all fuzz tests pass
- Slither + Semgrep — clean
- All invariants from Phase 2 covered by at least one proof or fuzz test

## The Iron Law

```
NO IMPLEMENTATION CODE WITHOUT TYPES AND INVARIANTS FIRST
```

Wrote a function body before defining its types? Delete it.
Wrote business logic before invariant scaffold? Delete it.

## Review Gates

### Per-File Review

After every file is created or modified, STOP and ask the user if they want to review before continuing. If yes, wait for review. Address ALL comments and pseudocode annotations before touching any other file.

```
Write/modify file -> Ask user to review -> User adds comments/pseudocode ->
Address ALL comments -> Ask user to re-review -> Repeat until approved ->
Next file
```

No batching. No "I'll fix those later." Every comment resolved before moving forward.

### Proofs One at a Time

Write ONE Kontrol proof -> kontrol build -> kontrol prove -> verify passes or fix -> user review -> THEN next proof. Never batch multiple proofs.

## Hard Constraints

- **No inheritance** in contracts (tests and scripts are exceptions)
- **SCOP philosophy**: no `library` keyword, no imports in contract files, file-level free functions, composition over inheritance
- **Spec Kit required**: every feature starts with /speckit.specify
- **Invariants-first**: scaffold written BEFORE implementation
- **Kontrol for formal verification**: Foundry tests as formal specs
- **Static analysis**: Slither + Semgrep with Decurity rules as gates
- **Per-file user review**: every file modification approved before proceeding
- **One proof at a time**: sequential, reviewed proof writing

## References

- Type-Driven Development with Idris (Edwin Brady) — core philosophy of encoding invariants in types
- Angstrom (SorellaLabs) — Solidity UDVT patterns: dimensional types, opaque construction, bit-packed layouts, variant maps
- Compose (Perfect-Abstractions) — SCOP philosophy: no inheritance, facet+mod, file-level free functions
- Trail of Bits — Invariant-Driven Development (blog.trailofbits.com/2025/02/12/the-call-for-invariant-driven-development/)
- Trail of Bits static-analysis skills — Slither + Semgrep workflow and rulesets
- Kontrol (Runtime Verification) — formal verification via symbolic execution of Foundry tests
- Spec Kit (GitHub) — spec-driven development workflow
