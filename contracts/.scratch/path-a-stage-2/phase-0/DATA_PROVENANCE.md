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

## Section: Task 0.2 — Notebook scaffolding + Python deps

**Owner:** Senior Developer (this dispatch — Task 0.2 executed inline alongside Task 0.1 per Phase-0 brief).
**Constructed:** 2026-05-02 18:10–18:15 EDT.
**Outputs:**
- `contracts/notebooks/pair_d_stage_2_path_a/Colombia/env.py` (path constants + REQUIRED_PACKAGES + Foundry pin + RPC ladder + Mento contract addresses + spec-pinned numerical constants)
- `contracts/notebooks/pair_d_stage_2_path_a/Colombia/refs.bib` (15 BibTeX entries: spec/plan/Stage-1 anchor + Carr-Madan 1998/2001 + Panoptic whitepaper + Panoptic SFPM addresses + Mento V3 docs + Mento canonical naming + Foundry v1.5.1 + 3 methodology citations)
- `contracts/notebooks/pair_d_stage_2_path_a/Colombia/requirements.txt` (12 dependency lines mirroring env.REQUIRED_PACKAGES, re-installable via `uv pip install -r`)
- `contracts/notebooks/pair_d_stage_2_path_a/Colombia/_nbconvert_template/{jupyter_nbconvert_config.py,article.tex.j2}` (mirrored from `fx_vol_cpi_surprise/Colombia/_nbconvert_template/`, env-module name updated from `fx_vol_env` → `path_a_env`)
- 4 notebook skeletons: `01_v0_sympy.ipynb` (4 cells), `02_v1_mento_fork.ipynb` (4 cells), `03_v2_panoptic_strip.ipynb` (4 cells), `04_v3_gbm_mc.ipynb` (5 cells — extra trio for the §10.3 default_rng pin). Each carries the required 4-part citation block per `feedback_notebook_citation_block` plus a TODO block enumerating the rung's spec §2 exit criteria.
- Empty artifact directories: `estimates/`, `figures/`, `pdf/` (created for downstream rung-specific output dropping)

### Source: contracts/.venv (Python 3.13.5)

The venv at `contracts/.venv/` was already provisioned for Stage-1 work (statsmodels + numpy + pandas + scipy + matplotlib + jupyter ecosystem). Task 0.2 added the Path-A-specific dependencies via `uv pip install`:

- **Sympy 1.14.0** — already present (verified at smoke test).
- **QuantLib 1.42.1** — already present.
- **nbformat 5.10.4** — newly installed via `uv pip install`.
- **nbconvert 7.17.1** — newly installed.
- **matplotlib 3.10.8** — newly installed.
- **bibtexparser 1.4.4** — newly installed (refs.bib parse-verified).
- **IPython 9.12.0** — newly installed.
- **ipykernel 7.2.0** — already present.
- **jupyter_client 8.8.0**, **jupyter_core 5.9.1**, **Jinja2 3.1.6**, **pandas 3.0.2** — already present.

Re-install verification: `uv pip install -r contracts/notebooks/pair_d_stage_2_path_a/Colombia/requirements.txt` returned `Audited 12 packages in 19ms` with zero conflicts.

### env.py REPL test (parents-fix verification)

Per spec convention (`feedback_*` memory), env.py uses `Path(__file__).resolve().parents[3]` to anchor `_CONTRACTS_DIR`. REPL test:
```
$ python -c "import env; print(env.SPEC_SHA256, env.FOUNDRY_COMMIT_SHA, env.NB_V0_SYMPY_PATH.parent.name)"
1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78  b0a9dd9ceda36f63e2326ce530c10e6916f4b8a2  Colombia
```
All references resolve. `CPO_FRAMEWORK_PATH` exists; `STAGE1_VERDICT_MD` exists.

### Notebook headless-execution verification

`jupyter nbconvert --to notebook --execute 01_v0_sympy.ipynb` ran clean, output captured:
```
env.py loaded from: .../pair_d_stage_2_path_a/Colombia/env.py
SPEC_SHA256: 1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78
SPEC_VERSION: v1.2.1
FOUNDRY_COMMIT_SHA: b0a9dd9ceda36f63e2326ce530c10e6916f4b8a2
Stage-1 anchor PRIMARY_OLS_SHA256 (READ-ONLY): d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
Notebook scaffold OK — Phase-0 only; Phase-1+ dispatches will populate trios.
```
The other 3 NBs share the same env-import code-cell shape; not separately executed (they would emit identical output).

### refs.bib parseability

`bibtexparser.load(open(refs.bib))` returned 15 entries with no syntax errors. Citation keys cover: (a) spec + plan + Stage-1 anchor; (b) CPO framework import; (c) Carr-Madan 1998 + 2001; (d) Panoptic whitepaper + SFPM addresses; (e) Mento V3 docs + canonical naming corrigendum; (f) Foundry v1.5.1 commit pin; (g) 3 methodology memories (anti-fishing, trio-checkpoint, citation-block).

### sha-pinnability

These Phase-0 notebook scaffold files are sha-pinnable:
```
sha256sum contracts/notebooks/pair_d_stage_2_path_a/Colombia/env.py
sha256sum contracts/notebooks/pair_d_stage_2_path_a/Colombia/refs.bib
sha256sum contracts/notebooks/pair_d_stage_2_path_a/Colombia/requirements.txt
```

The 4 notebook skeletons themselves are NOT pinned by sha — they are scaffolds that Phase 1-4 dispatches will rewrite under trio discipline. The refs.bib + env.py + requirements.txt are the load-bearing scaffold files.

End of Task 0.2 section.
