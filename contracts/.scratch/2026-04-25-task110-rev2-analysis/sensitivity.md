# Sensitivity — Task 11.O Rev-2 Phase 5b

**Spec:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` §6 + §10  

---

## 1. Cross-row coefficient comparison (Rows 1 vs 3 vs 4: primary vs LOCF-excluded vs IMF-only)

| Row | Label | n | β̂ | SE | sign | gate | pre-committed |
|---|---|---|---|---|---|---|---|
| 1 | Primary | 76 | -2.799e-08 | 1.423e-08 | − | **FAIL** | OPEN (gate target) |
| 3 | LOCF-tail-excluded | 65 | -1.894e-08 | 1.602e-08 | − | **FAIL** | FAIL pre-registered (N < 75) |
| 4 | IMF-IFS-only | 56 | -1.548e-08 | 1.497e-08 | − | **FAIL** | FAIL pre-registered (N < 75 + power < 0.80) |

### 1.1 Sign / magnitude / significance variations

- **Sign:** CONSISTENT
- **Magnitude (Row 1 β̂ vs Row 3 β̂):** ratio = 0.676771
- **Magnitude (Row 1 β̂ vs Row 4 β̂):** ratio = 0.553274
- **Significance:** Row 1 = FAIL; Row 3 = FAIL; Row 4 = FAIL.
- **Pre-registered FAIL discipline:** Rows 3 + 4 are pre-registered to FAIL on N_MIN. They contribute pure-discipline anti-fishing locks, not gate-bearing evidence.

### 1.2 Bootstrap reconciliation (Row 2 vs Row 1 HAC) — spec §4.1 AGREEMENT criterion

- **HAC(4) 90% CI on β̂:** [-5.140e-08, -4.572e-09]
- **Bootstrap empirical 90% CI on β̂:** [-5.821e-08, 1.879e-09]
- **Containment ratio:** 0.779
- **AGREEMENT (≥ 0.50):** **AGREE**
- **FX-vol prior-art carry-forward:** FX-vol §3.5 found HAC + bootstrap AGREE; this run **also AGREES**

---

## 2. Robustness rows (5, 6, 11, 12, 13, 14)

### Row 5 — Lag sensitivity (X_d_{t-1})

- **n:** 75; **β̂:** 4.260e-09; **SE:** 1.704e-08; **gate:** **FAIL**; **relative to primary:** diverges by > 1·SE.

### Row 6 — Parsimonious controls (3-control: VIX + oil + intervention)

- **n:** 76; **β̂:** -7.317e-09; **SE:** 1.091e-08; **gate:** **FAIL**; **relative to primary:** diverges by > 1·SE.

### Row 11 — Student-t innovations refit

- **n:** 76; **β̂:** -2.799e-08; **SE:** 1.904e-08; **gate:** **FAIL**; **relative to primary:** within 1·SE.

### Row 12 — HAC(12) bandwidth sensitivity

- **n:** 76; **β̂:** -2.799e-08; **SE:** 1.061e-08; **gate:** **FAIL**; **relative to primary:** within 1·SE.

### Row 13 — First-differenced (Δlog X_d, ΔY₃)

- **n:** 75; **β̂:** -0.002155; **SE:** 0.001887; **gate:** **FAIL**; **relative to primary:** diverges by > 1·SE.

### Row 14a — WC-CPI weights (50/30/20)

- **n:** 76; **β̂:** -2.919e-08; **SE:** 1.718e-08; **gate:** **FAIL**; **relative to primary:** within 1·SE.

### Row 14b — WC-CPI weights (60/25/15) [primary]

- **n:** 76; **β̂:** -2.978e-08; **SE:** 1.911e-08; **gate:** **FAIL**; **relative to primary:** within 1·SE.

### Row 14c — WC-CPI weights (70/20/10)

- **n:** 76; **β̂:** -3.038e-08; **SE:** 2.123e-08; **gate:** **FAIL**; **relative to primary:** within 1·SE.

---

## 3. Diagnostic rows (7, 8) — under-N

### Row 7 — Arb-only diagnostic (BancorArbitrage trader)

- **n:** 45 (under-N diagnostic); **β̂:** -3.410e-08; **gate:** **FAIL** (informational only).

### Row 8 — Per-currency COPM diagnostic (Mento Colombian Peso leg)

- **n:** 47 (under-N diagnostic); **β̂:** -1.634e-07; **gate:** **FAIL** (informational only).

