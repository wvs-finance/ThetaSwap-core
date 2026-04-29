# Pair D — robustness pack R1-R4 results (NB03 §5)

Spec sha256 (pinned, §9.1 immutable): `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659` (v1.3.1)
Panel sha256 (pinned): `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`
Primary OLS json sha256 (NB02 hand-off): `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf`
Robustness pack json sha256 (this NB output, round-tripped in §6): `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904`

## Primary reference (NB02 §2)

β̂_composite (primary) = **+0.1367** (HAC SE 0.0247, p_one = 1.46e-08, sign = `+`).

## R-row results table (computed by NB03 trios 1–4; byte-identical to robustness_pack.json)

| R-row | β̂_composite | HAC SE | t-stat | p_one | Sign | vs primary |
|-------|-------------|--------|--------|-------|------|------------|
| R1 | +0.0815 | 0.0581 | +1.403 | 8.03e-02 | `+` | AGREE |
| R2 | +0.4489 | 0.0721 | +6.223 | 2.44e-10 | `+` | AGREE |
| R3 | +0.0313 | 0.0056 | +5.543 | 1.49e-08 | `+` | AGREE |
| R4 | +0.1367 | 0.0266 | +5.140 | 1.38e-07 | `+` | AGREE |

## §7.1 sign-consistency classification (spec-pinned)

- Primary sign: `+`
- Per-row signs: R1=`+`, R2=`+`, R3=`+`, R4=`+`
- Sign-flips vs primary: **0 of 4**
- §7.1 classification: **AGREE**
- §3.5 SUBSTRATE_TOO_NOISY trigger (≥3 flips): **does NOT fire**

## Independence-strength caveat (RC NIT #4, honest interpretation)

The 4-row §7.1 count is the spec-pinned classification arithmetic that drives the §8.1 verdict tree. For honest interpretation of substrate stability strength, note that:

- **R1 (2021 regime dummy)** and **R2 (Y_narrow J+M+N)** are *truly independent* design variations that probe distinct potential confounds (methodology break + sectoral concentration of mechanism).
- **R3 (raw OLS, no logit)** is a *near-tautological* rescaling: empirical t-stat matched primary's to within 0.003 (β̂_primary / β̂_R3 ≈ 4.366× = local logit derivative `1/[Ȳ(1-Ȳ)] ≈ 4.351` at Ȳ ≈ 0.642).
- **R4 (HAC NW=12)** is *bandwidth-only*: point estimate identical to primary by construction; only SE differs.

- 4-row sign-flip count (spec-pinned, drives verdict tree): **0/4** → **AGREE**
- 2-row independent-evidence count (R1 + R2 only): **0/2** → both readings concur on substrate stability.

## Anti-fishing compliance (spec §9)

- Each R-row varies exactly one design choice from primary per spec §7 line 200.
- No multi-dimensional re-specification.
- Sign + p reported as computed; no verdict pre-judgment.
- §7.1 thresholds (AGREE/MIXED/DISAGREE; SUBSTRATE_TOO_NOISY ≥3 flips) are spec-pinned per §9.1 immutability invariant; not adjustable post-data.

## Hand-off to §6 (joint-verdict gate)

R-consistency = **AGREE** → §8.1 step 2 does NOT trigger SUBSTRATE_TOO_NOISY override; primary (NB02) verdict propagates per §8.1 step 4(a).
