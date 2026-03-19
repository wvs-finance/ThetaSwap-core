# Frozen Data

All datasets backing the ThetaSwap fee concentration model, frozen as of **2026-03-05**.

## Canonical JSON Format

Every file in this directory has the following top-level structure:

```json
{
  "metadata": { ... },
  "data": [ ... ]
}
```

The SHA-256 hash stored in `metadata.sha256` is computed over the `data` field **only**, after canonicalization:

- Keys sorted lexicographically (recursive)
- No extra whitespace (compact serialization)

To verify: `uhi8/bin/python research/data/scripts/verify_provenance.py`

## Dataset Table

| File | Source | Query ID | Description |
|------|--------|----------|-------------|
| `il_proxy.json` | derived | N/A | 41-day IL proxy for ETH/USDC 30bps. Original label: Q5. |
| `daily_at.json` | dune | 6783604 | Daily real A_T and null A_T from per-position fees. ETH/USDC 30bps, Dec 5 2025 – Jan 14 2026. |
| `positions.json` | frozen_original | N/A (reconstruction: 6847717) | 600 position exits. Original Q4v2 query lost; NFT reconstruction confirms directional robustness. |
| `selected_pools.json` | subgraph | N/A | 10 V3 pools selected via top-100-by-TVL, 2-4-4 stratification. |
| `cross_pool_concentrations.json` | dune | 6784588 | A_T per pool over 90-day window. Parameterized ×10 pools. |
| `per_position_fees.json` | dune | 6815916 | 50 per-position lifetime fees, ETH/USDC 0.3%, Dec 20-26 2025. |
| `fci_v4_events.json` | dune | 6795594 | 107 V4 pool events for FCI differential testing. Block range 23656000-23668000. |

## IL_MAP Derivation

`il_proxy.json` contains the daily impermanent loss proxy for the ETH/USDC 30bps pool. The original query label was Q5 but no Dune query ID was preserved. The data is treated as derived — hash-only verification.

## RAW_POSITIONS Reconstruction Note

The original Q4v2 Dune query is lost. An NFT-based reconstruction (Dune 6847717) was created using NonfungiblePositionManager events, producing 618 rows with ~4x larger blocklife values. Econometric comparison confirms directional robustness: beta_a_t same sign and significance (see `tmp/econometrics-comparison-report.md`).

The file `positions.json` contains the original frozen 600-row dataset (source: `frozen_original`). The reconstruction query (6847717) is documented in `research/data/queries/README.md` for audit purposes but its output is not frozen here.

## Verification

Run `uhi8/bin/python research/data/scripts/verify_provenance.py` to verify all hashes.

The script checks each file's `metadata.sha256` against a freshly computed hash of its canonicalized `data` field and reports any mismatches.

## Data Freeze Date

All data frozen as of **2026-03-05**.
