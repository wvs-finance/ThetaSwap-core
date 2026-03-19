# FCI Token Vault — Invariants

> 17 invariants. INV-014 (single-sided redemption solvency) deferred.

| ID | Description | Category | Hoare Triple | Verification |
|---|---|---|---|---|
| INV-001 | deltaPlusToSqrtPriceX96 round-trips | Function-level | {δ⁺ ∈ [0, Q128)} → f(δ⁺) ∈ [MIN_SQRT_PRICE, MAX_SQRT_PRICE] | Kontrol + fuzz |
| INV-002 | δ⁺=0 maps to SQRT_PRICE_1_1 | Function-level | {δ⁺=0} → f(0) = 2⁹⁶ | Kontrol |
| INV-003 | δ⁺ monotonicity | Function-level | {a < b} → f(a) ≥ f(b) | Fuzz |
| INV-004 | applyDecay never exceeds input | Function-level | {hwm, dt ≥ 0} → decay(hwm, dt) ≤ hwm | Kontrol + fuzz |
| INV-005 | applyDecay(hwm, 0) = hwm | Function-level | {dt=0} → decay(hwm, 0) = hwm | Kontrol |
| INV-006 | updateHWM only increases | Function-level | {hwm, price} → max(hwm, price) ≥ hwm | Kontrol |
| INV-007 | computePayoff ≥ 0 | Function-level | {any inputs} → payoff ≥ 0 | Kontrol + fuzz |
| INV-008 | computePayoff = 0 when hwm ≤ strike | Function-level | {hwm ≤ strike} → payoff = 0 | Kontrol |
| INV-009 | computePayoff capped at Q96 | Function-level | {any inputs} → payoff ≤ 2⁹⁶ | Fuzz |
| INV-010 | Multi-round FCI accumulation | System-level | {K rounds, JIT enters each} → Δ⁺_K > Δ⁺_1 | Fork test |
| INV-011 | Hedged LP payout ≥ unhedged LP payout | System-level | {vault settles} → hedgedPayout ≥ unhedgedPayout | Fork test |
| INV-012 | Token supply: LONG.totalSupply = SHORT.totalSupply | System-level | {any state} → long.totalSupply() == short.totalSupply() | Kontrol |
| INV-013 | Vault balance ≥ total deposits | System-level | {no redemptions} → vault.balance ≥ totalDeposits | Kontrol |
| INV-014 | Single-sided redemption solvency | System-level | DEFERRED — requires separate accounting model | — |
| INV-015 | Only vault can mint tokens | Type-level | {caller ≠ vault} → mint reverts | Kontrol |
| INV-016 | settle() requires expiry passed | System-level | {block.timestamp < expiry} → settle reverts | Kontrol |
| INV-017 | redeem() requires settled | System-level | {!settled} → redeem reverts | Kontrol |
