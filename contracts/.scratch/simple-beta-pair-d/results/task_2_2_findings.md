# Task 2.2 — Robustness pack R1-R4 findings

Spec sha256: `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659` (v1.3.1)
Panel sha256: `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`
Primary OLS json sha256: `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf`
This file's parent JSON sha256: `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904`

**Primary reference (Task 2.1):** β_composite = +0.1367 (HAC SE 0.0247, p_one = 1.46e-08, sign = +).

## R1 — 2021 regime dummy (§6 alternative disposition)

*Implementation:* primary regressors {const, lag6, lag9, lag12} + `marco2018_dummy_t` (1 if t ≥ 2021-01-01; 62 ones in N=134). Per DATA_PROVENANCE.md line 268, the DANE empalme is structurally pre-baked into `FEX_C` for 2015-2020; algebraic identity confirms Y_raw is invariant to any uniform monthly empalme scalar (numerator + denominator cancel). R1 therefore = primary + dummy at the OLS stage.

β_composite = **+0.0815** (HAC SE 0.0581, t = +1.403, p_one = 8.03e-02, sign = **+** vs primary `+` → **AGREE**).

## R2 — Y narrow (CIIU Rev. 4 J+M+N, BPO-narrow)

*Implementation:* primary regressors unchanged; dependent variable swapped from `Y_broad_logit` to `Y_narrow_logit`. Y_narrow has empirical range ≈ [0.07, 0.12] (interior to (0,1); logit valid).

β_composite = **+0.4489** (HAC SE 0.0721, t = +6.223, p_one = 2.44e-10, sign = **+** vs primary `+` → **AGREE**).

## R3 — Raw OLS (no logit transform)

*Implementation:* primary regressors unchanged; dependent variable swapped from `Y_broad_logit` to `Y_broad_raw` (level share, range ≈ [0.60, 0.68]).

β_composite = **+0.0313** (HAC SE 0.0056, t = +5.543, p_one = 1.49e-08, sign = **+** vs primary `+` → **AGREE**). Coefficient magnitudes are smaller in level-units than logit-units, as expected.

## R4 — HAC bandwidth L=12

*Implementation:* identical primary OLS; HAC `maxlags=12` instead of the rule-of-thumb 4. β̂_composite is mechanically unchanged (+0.1367 = primary +0.1367); only HAC SE changes.

β_composite = **+0.1367** (HAC SE 0.0266, t = +5.140, p_one = 1.38e-07, sign = **+** vs primary `+` → **AGREE**).

## R-consistency verdict (§7.1)

Primary sign: `+`

| R-row | Sign | Match vs primary |
|-------|------|------------------|
| R1 | `+` | AGREE |
| R2 | `+` | AGREE |
| R3 | `+` | AGREE |
| R4 | `+` | AGREE |

**Number of sign-flips:** 0 of 4. **Verdict per §7.1:** **AGREE**.

**SUBSTRATE_TOO_NOISY (§3.5) does NOT fire** (only 0/4 flips; trigger requires ≥3). Primary verdict from §3.1 (PASS) is preserved into Task 2.3.

*Anti-fishing compliance:* each R-row varies exactly one design choice from the primary per spec §7 line 200. No multi-dimensional re-specification. Sign + p reported as computed; no verdict pre-judgment.
