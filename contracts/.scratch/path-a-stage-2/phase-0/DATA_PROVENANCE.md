# DATA_PROVENANCE.md — Path A Stage-2 Phase 0 artifacts

This file documents the source, transformation, and lineage of every artifact
emitted by Phase 0 of the Path A (fork-and-simulate) implementation plan. Each
Task appends its own section. Sections are independent — no Task overwrites
another Task's content.

**Governing artifacts (frozen):**
- Spec: `contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-A-fork-simulate-spec.md` (sha256 `1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78`, v1.2.1)
- Plan: `contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-A-fork-simulate-implementation.md` (sha256 `05f5216faa62b7a3cccb384215d5da007636d87d2b6d9597a21cb42b4860436d`)
- Stage-1 PASS verdict (READ-ONLY anchor): `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/VERDICT.md` (sha256 `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf`)

---

## Section: Task 0.1 — Foundry pin + environment smoke test

**Owner:** Senior Developer (Phase 0 task 0.1 dispatch agent — this dispatch's executor)
**Constructed:** 2026-05-02 18:03–18:05 EDT (single foreground session)
**Outputs:**
- `contracts/.scratch/path-a-stage-2/phase-0/foundry_pin.md` (Foundry/Anvil/Cast version pin + commit SHA + install method + host environment)
- `contracts/.scratch/path-a-stage-2/phase-0/environment_smoke_test.md` (reachability matrix + 34-second Anvil fork smoke for Celo + Ethereum + empirical CU baseline for 3 RPC methods + free-tier feasibility surfaces)

### Source: locally installed Foundry binaries

- **Path:** `~/.foundry/bin/{forge,anvil,cast,chisel,foundryup}`
- **Install method:** `foundryup` (no rust local build).
- **Commit SHA (determinism anchor):** `b0a9dd9ceda36f63e2326ce530c10e6916f4b8a2` for all four binaries (single Foundry monorepo commit).
- **Build timestamp:** 2025-12-22T11:39:01Z (Build Profile maxperf).

### Source: free-tier RPC endpoints (probed at smoke test time)

- **Alchemy free-tier Ethereum:** `https://eth-mainnet.g.alchemy.com/v2/$ALCHEMY_API_KEY` (app `4idrlqy09oetrckh`, Ethereum enabled). Reachable; chainId 1 confirmed.
- **Alchemy free-tier Celo:** SAME app — Celo Mainnet NOT enabled at smoke time (HTTP 403 with explicit "CELO_MAINNET is not enabled for this app" message, dashboard URL provided). Surface flagged for orchestrator: enable Celo on app OR provision separate app OR accept Forno-as-PRIMARY for v1.
- **Public Forno Celo:** `https://forno.celo.org` (cLabs-operated public endpoint, no API key, no SLA). Reachable; chainId 0xa4ec (42220) confirmed. **Header note:** default Python `urllib` User-Agent triggers 403; v1 harness Python code MUST set explicit non-default UA.
- **Public llamarpc Ethereum:** `https://eth.llamarpc.com` (no API key). Reachable; chainId 1 confirmed; head block 25010149 returned.
- **Public Ankr Ethereum:** `https://rpc.ankr.com/eth` — REQUIRES API KEY as of 2026-05-02 (no longer free for unauthenticated requests). Spec §5 enumeration is partially stale; recommended Ethereum FALLBACK is `eth.llamarpc.com`.

### Smoke test fork-block samples (NOT binding pins for v1/v2 dispatch)

- **Celo sample fork block:** 65800000 (head was 65858613 at smoke time; `65800000` chosen as a recent-but-not-tip block for fork stability). Anvil fork against Forno at this block: 34-second uptime, two `cast block-number` probes returned 65800000 byte-identically, no rate-limit hits.
- **Ethereum sample fork block:** 25000000 (head was 25010148 at smoke time). Anvil fork against Alchemy at this block: 34-second uptime, two probes returned 25000000 byte-identically, block hash `0xf398976165ca4756c77fc6b61111fa1102d431eb03082417ecce38b36308d728`, no rate-limit hits.

These sample fork blocks will NOT be inherited by v1 / v2 dispatch. Per spec §10.1, v1 / v2 each pin their own fork-block height at v-dispatch time, recorded in their respective fork manifests with a rate-limit-headroom note.

### Empirical CU consumption sample (per Wave-1 RC FLAG-P1)

Probed against Alchemy free-tier Ethereum, single-call (no batching):

| Method | Latency (wall clock) | CU cost (Alchemy public table) |
|---|---|---|
| `eth_call` (ERC20 balanceOf USDC) | 274 ms | 26 CU |
| `eth_getStorageAt` (USDC slot 0) | 286 ms | 17 CU |
| `eth_getLogs` (USDC Transfer 1-block range, 67 logs returned) | 495 ms | 75 CU base + per-log variable |

Source for CU figures: `https://docs.alchemy.com/reference/compute-unit-costs` (snapshot 2026-05-02; orchestrator should re-verify at v2 dispatch time as Alchemy adjusts the table without notice). Empirical-vs-public-table verification (controlled-burn dashboard meter) deferred to v2 dispatch IF rate-limit headroom analysis suggests <20% margin on any cap.

### Verification status of feasibility surfaces

Three free-tier feasibility surfaces flagged (full detail in `environment_smoke_test.md` §6):
1. Alchemy app does not have Celo enabled — orchestrator-actionable.
2. Forno requires custom User-Agent (default Python urllib UA returns 403) — code-implication for v1 harness.
3. Public Ankr no longer free without API key — spec §5 partially stale; `eth.llamarpc.com` is the recommended Ethereum FALLBACK.

None block Phase 0 commit. Gate B0 3-way review (Task 0.3) adjudicates whether any require pre-Phase-1 remediation.

### sha-pinnability

These Phase-0 artifacts are sha-pinnable. Compute via:
```
sha256sum contracts/.scratch/path-a-stage-2/phase-0/foundry_pin.md
sha256sum contracts/.scratch/path-a-stage-2/phase-0/environment_smoke_test.md
sha256sum contracts/.scratch/path-a-stage-2/phase-0/DATA_PROVENANCE.md
```

Downstream version manifests (v1 fork manifest under Task 2.2; v2 under Task 3.2; v3 under Task 4.2) will cite the foundry_pin.md sha256 verbatim per spec §10.2.

---

## Section: Task 0.2 — Notebook scaffolding + Python deps (appended below by the Task 0.2 executor)

(populated by Task 0.2 commit)
