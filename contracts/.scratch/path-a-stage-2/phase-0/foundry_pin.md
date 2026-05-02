# Foundry / Anvil / Cast Version Pin — Path A Stage-2 Phase 0 Task 0.1

**Captured:** 2026-05-02 PM
**Spec sha pin:** `1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78` (v1.2.1)
**Plan sha pin:** `05f5216faa62b7a3cccb384215d5da007636d87d2b6d9597a21cb42b4860436d`
**Free-tier discipline pin:** spec §5 + §10.1 — Alchemy free ≈30M CU/mo + ≈25 req/sec sustained + ≈500 CU/sec rolling-window cap; public-RPC fallback (`https://forno.celo.org` for Celo, `https://eth.llamarpc.com` for Ethereum)

---

## §1. Pinned versions (commands actually run)

| Tool   | Version string | Commit SHA |
|--------|----------------|------------|
| forge  | `forge Version: 1.5.1-stable` (Build Timestamp 2025-12-22T11:39:01Z, Build Profile maxperf) | `b0a9dd9ceda36f63e2326ce530c10e6916f4b8a2` |
| anvil  | `anvil Version: 1.5.1-stable` (Build Timestamp 2025-12-22T11:39:01Z) | `b0a9dd9ceda36f63e2326ce530c10e6916f4b8a2` |
| cast   | `cast Version: 1.5.1-stable` (Build Timestamp 2025-12-22T11:39:01Z) | `b0a9dd9ceda36f63e2326ce530c10e6916f4b8a2` |

All three binaries reside under `~/.foundry/bin/` (timestamp `2026-01-15 15:56`, sizes 34–72 MB). The single Foundry monorepo commit `b0a9dd9c…b8a2` is the determinism anchor (per spec §10.2).

## §2. Source URL + install method

- **Source URL:** https://github.com/foundry-rs/foundry (commit `b0a9dd9c…b8a2`).
- **Install method:** `foundryup` (the maintainer-distributed installer at `~/.foundry/bin/foundryup`, 24,676 bytes). `foundryup` pulls pre-compiled binaries for the host triple from the foundry release archive and drops them into `~/.foundry/bin/`. This is the standard install path; no rust toolchain build occurred locally.
- **Re-install reproducibility:** to re-pin at the same commit, run `foundryup --commit b0a9dd9ceda36f63e2326ce530c10e6916f4b8a2`. Per spec §10.2, the commit hash is the determinism anchor — the version string `1.5.1-stable` alone is insufficient because `stable` is a moving tag.

## §3. Host environment (OS + arch)

- **Kernel:** `Linux archbox 6.18.9-arch1-2 #1 SMP PREEMPT_DYNAMIC Mon, 09 Feb 2026 17:16:33 +0000 x86_64 GNU/Linux`
- **Distro:** Arch Linux (rolling, build_id `rolling`)
- **System Python:** `/usr/bin/python3 → Python 3.14.3` (used for ad-hoc CU baseline scripts in Task 0.1; the notebook venv is pinned separately under Task 0.2)

## §4. Compatibility note vs spec §10.2 pin requirement

Spec §10.2 requires Foundry/Anvil version pins recorded in **each version manifest** (v1, v2, v3 manifests). This Phase-0 file is the upstream source-of-truth that those manifests cite. The commit hash `b0a9dd9c…b8a2` will be carried verbatim into:

- `contracts/.scratch/path-a-stage-2/results/path_a_v1_fork_manifest.md` (Task 2.2)
- `contracts/.scratch/path-a-stage-2/results/path_a_v2_fork_manifest.md` (Task 3.2)
- `contracts/.scratch/path-a-stage-2/results/path_a_v3_reproducibility_manifest.md` (Task 4.2)

Re-pinning to a different Foundry commit between v0 and v3 is a CORRECTIONS-block-requiring change per spec §10.1 fork-block rule (commit hash is part of the determinism manifold; changing it requires re-execution of all downstream artifacts).

## §5. No paid services involved

`foundryup` and the Foundry binaries themselves are free (GPL/MIT licensed, distributed at no cost). Per CORRECTIONS-δ free-tier-only budget pin, no paid tier triggered for Foundry installation.

## §6. DATA_PROVENANCE mirror

This file is sha-pinnable; downstream version manifests cite this file by sha256. To compute:
```
sha256sum contracts/.scratch/path-a-stage-2/phase-0/foundry_pin.md
```

End of foundry_pin.md.
