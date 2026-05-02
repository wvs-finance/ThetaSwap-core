# Pair D Stage-2 Path B — Phase 0 Task 0.1 — Stage-1 sha-pin verify

**Author:** Data Engineer dispatch (Phase 0 scaffolding)
**Run timestamp UTC:** 2026-05-02T22:01Z
**Verification host:** local (worktree `phase0-vb-mvp`)
**Plan reference:** `contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md`
**Spec reference (Path B):** `contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md` (sha pin in plan frontmatter: `4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea`)

## §1 — Scope

Verify that the five Stage-1 sha pins listed in the plan frontmatter `stage1_pinned_chain` block correspond to the live committed artifacts in this worktree. Per spec §3.A and per `feedback_real_data_over_mocks`, every Path B downstream artifact will reference these pins; a mismatch HALTS Phase 0 under `Stage2PathBStage1ChainBroken` (typed exception per spec §6, raised as user-adjudicated HALT since this exception is not in the pre-pinned list).

Stage-1 pin chain is **READ-ONLY** through Path B execution; no modification of any Stage-1 artifact is permitted under this plan.

## §2 — Pinned values (from plan frontmatter `stage1_pinned_chain`)

| field | pinned sha256 |
|---|---|
| `pair_d_spec_v1_3_1` | `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659` |
| `panel` | `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf` |
| `primary_ols` | `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf` |
| `robustness_pack` | `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904` |
| `verdict` | `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf` |

## §3 — Live computation method

For data artifacts (panel, primary_ols, robustness_pack, verdict): direct file `sha256sum`.

For the Pair D Stage-1 spec (`contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md`), the pinned value is computed via the spec's self-referential protocol pinned at line 4: replace the inline `decision_hash` field's pinned value with the sentinel string `<to-be-pinned-after-CORRECTIONS-alpha-prime-3way-cleanup>` and recompute sha256 of the resulting bytes. A direct sha256 of the as-committed file does NOT match the pinned value by design (the pinned value would be self-circular otherwise).

## §4 — Verification results

| pin | status | live value | reconciliation note |
|---|---|---|---|
| `pair_d_spec_v1_3_1` | **MATCH** | `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659` (recomputed via self-referential protocol) | direct file sha = `fdd90fc78c733493a3d67a8cb2cff45236dd3f9744d36619f3b4cdd9e7f9bc37`; this is expected per the protocol pinned in spec line 4. Self-referential recompute matches the pinned value. |
| `panel` | **MATCH** | `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf` | direct sha256sum of `contracts/.scratch/simple-beta-pair-d/data/panel_combined.parquet` |
| `primary_ols` | **MATCH** | `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf` | direct sha256sum of `contracts/.scratch/simple-beta-pair-d/results/primary_ols.json` |
| `robustness_pack` | **MATCH** | `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904` | direct sha256sum of `contracts/.scratch/simple-beta-pair-d/results/robustness_pack.json` |
| `verdict` | **MATCH** | `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf` | direct sha256sum of `contracts/.scratch/simple-beta-pair-d/results/VERDICT.md` |

**Result: 5 / 5 pins verified. No `Stage2PathBStage1ChainBroken` HALT triggered. Phase 0 may proceed.**

## §5 — Provenance

- Panel commit: `37b2fb361 data(abrigo): Pair D Phase 1 panel — Y_broad+Y_narrow+X joint, N=134 post-lag-12`
- Spec v1.3.1 commit: `21beffade spec(abrigo): CORRECTIONS-α' v1.3.1 — Pair D window 2010→2015 per Task 1.1 Step 1 HALT`
- Verdict commit: `9c0eebfdf` (per CLAUDE.md Pair D PASS verdict block)

## §6 — Read-only invariant

This verification step performs `sha256sum` reads only. No artifact under `contracts/.scratch/simple-beta-pair-d/`, no Stage-1 spec, and no Stage-1 plan was modified by this task. The `feedback_strict_tdd` and `feedback_real_data_over_mocks` invariants are upheld trivially (no synthesis, no mock; bit-for-bit re-hashing of committed files).

## §7 — Next task

Task 0.2: DuckDB + Polars + pyarrow Python deps install + version pin recording. Task 0.3: Network config (SQD + Alchemy + public-RPC fallback) + burst-rate harness. Task 0.4: Notebook scaffolding. Gate B0: 3-way review.
