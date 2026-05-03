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

---

## Section: Task 1.1 — TDD failing-test scaffold for v0 exit criteria

**Owner:** Senior Developer (Phase 1 Task 1.1 dispatch agent — this dispatch's executor)
**Constructed:** 2026-05-03 02:32 UTC (single foreground session)
**Outputs:**
- `contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py` — pytest module with 5 failing tests (sub-criteria a-e from spec §2 v0)
- `contracts/.scratch/path-a-stage-2/phase-1/v0_test_run.md` — captured `pytest --tb=short -v` output showing 5 FAILED (not 5 ERROR), with provenance pins + failure-mode classification + caveats

**Pre-existing fixture consumed:**
- `contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py` — stub module raising `NotImplementedError` on every API call. Untracked at dispatch start; provides the seam against which Tasks 1.2 + 1.3 + 1.4 (Analytics Reporter notebook trios) will hang real implementations.

### Source: spec §2 v0 sub-criteria (a)-(e)

The 5 tests are derived 1-to-1 from spec §2 v0 (lines 124-126):
- (a) `Δ^(a_l) > 0` over admissible `0 < ε < 1` → `test_a_delta_a_l_sign_positive`
- (b) `Δ^(a_s) < 0` over same domain → `test_b_delta_a_s_sign_negative`
- (c) `Π(σ_T) = -∫₀^σ_T Δ^(a)(u) du` yields `K·√σ_T` both sides → `test_c_pi_closed_form_equilibrium_k_l_eq_k_s`
- (d) Linearization `Π ≈ K̂·σ_T` with `K̂ = K*/(2√σ₀)` → covered by combined (c) + (e) coverage; the §11.a self-consistency two-impl check serves as the explicit (d)-equivalent → `test_d_self_consistency_two_independent_codes`
- (e) Carr-Madan strip identity 12-leg approx vs analytic per §11 → `test_e_carr_madan_strip_reconciles_within_truncation_bound`

Spec §10.5 (3 condors × 4 legs = 12 legs total), §11.a (`SELF_CONSISTENCY_TOL = 1e-10 × 12 = 1.2e-9`), §11.b (`TRUNCATION_BOUND_REL = 5e-2` at GBM σ_0 = 10% baseline) supply the numerical thresholds in the test bodies.

### Source: imported CPO framework note

Framework note `contracts/notes/2026-04-29-macro-markets-draft-import.md` lines 130-272 supplies:
- `(X/Y)_t(ε,ω)` deterministic perturbation generator (lines 130-138)
- `σ_T(ε,ω)` and `ε(σ_T)` inversion (lines 142-155)
- `Δ^(a_l) > 0` and `Δ^(a_s) < 0` symbolic claims (lines 161-179, with explicit "verification of `Δ^(a_s) < 0` is not trivial" flag at line 179)
- `Π = K·√σ_T` closed forms on both sides + equilibrium `K_l = K_s` (lines 209-227)
- Linearization `Π ≈ K̂·σ_T`, `K̂ = K*/(2√σ_0)` (lines 247-256)
- Carr-Madan log-contract identity (lines 258-272)
- 3-condor / 12-leg discrete strip approximation (lines 276-326)

The note is byte-identical to source `~/learning/cfmm-theory/macro-markets/DRAFT.md` per spec §3.

### Source: contracts/.venv (Python 3.13.5)

No new dependencies installed for Task 1.1. The test scaffold consumes only the Phase-0-pinned stack:
- pytest 9.0.3 (from `contracts/.venv`)
- sympy 1.14.0 (Phase 0 Task 0.2 baseline)
- numpy 2.4.4, scipy 1.17.1 (Phase 0 Task 0.2 baseline)

### Verification status

- **Test collection:** 5 of 5 tests collected cleanly (zero collection errors)
- **Test execution:** 5 of 5 tests FAILED with explicit `NotImplementedError` traceback citing spec sub-criterion verbatim (zero ERROR results)
- **pytest exit code:** 1 (standard for any test failure)
- **Failure-mode classification:** all 5 are FAILED (test body executed, assertion path reached) — NOT ERROR (collection / fixture failure). This satisfies the `feedback_strict_tdd` requirement that failing tests be authored BEFORE implementation.

### Free-tier compliance

- Pure offline pytest invocation
- Zero network calls
- Zero Alchemy compute units consumed
- Zero Forno hits
- Zero Anvil fork spawned
- `Stage2PathABudgetOverrun` not at risk

### Caveat: dispatch-brief vs plan §3 path mismatch

Dispatch brief instructs `contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py`; plan §3 Phase 1 Task 1.1 instructs `contracts/.scratch/pair-d-stage-2-path-a/tests/test_v0_exit_criteria.py`. Dispatch brief is authoritative for THIS execution; honored as such. No file is created at the plan-path location. If Phase 5 Task 5.1 (Reality Checker) flags this as a path-conflict between plan and brief, follow-up CORRECTIONS-block can harmonize — out of scope for Task 1.1.

### sha-pinnability

These Phase-1 Task 1.1 artifacts are sha-pinnable. As of construction time:

```
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py
  sha256: 9d34098ff3f3ddbdb17f9881734b0b9c7fde78d6b516661a379abd08caea551e
contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py
  sha256: df76e068e12b83ac86fbada4696b246f8b10ac09211c71079975917b2bc94e4a
```

Re-compute via:
```
sha256sum contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py
sha256sum contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py
sha256sum contracts/.scratch/path-a-stage-2/phase-1/v0_test_run.md
```

The `v0_sympy.py` stub will be REPLACED by the sympy-pickled expression-tree artifacts emitted by the Analytics Reporter notebook trios in Tasks 1.2 + 1.3 (per plan §3 outputs `path_a_v0_delta_expressions.pkl` and `path_a_v0_derivation.pkl`). The test scaffold itself (`test_v0_exit_criteria.py`) is expected to be invariant from this point through Phase 1 Gate B1: any modification to the test bodies is a spec-amendment-equivalent action that triggers `Stage2PathAFrameworkInternallyInconsistent` HALT-disposition per `feedback_strict_tdd`.

End of Task 1.1 section.

---

## Section: Phase 1 Task 1.2 Trio 1 — Symbolic Δ^(a_l) / Δ^(a_s) derivation

**Owner:** Analytics Reporter (Phase 1 Task 1.2 Trio 1 dispatch agent — this dispatch's executor)
**Constructed:** 2026-05-02 EDT (single foreground session under auto mode)
**Outputs:**
- `contracts/notebooks/pair_d_stage_2_path_a/Colombia/01_v0_sympy.ipynb` (3 trio cells inserted after env scaffold cell 2; new cell count = 7)
- `contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py` (replaced 2 of 8 NotImplementedError stubs with canonical sympy expressions: `delta_a_l_expr`, `delta_a_s_expr`)

### Source: framework derivation `contracts/notes/2026-04-29-macro-markets-draft-import.md`

- **Lines 10-17**: cash-flow definition `CF_T^(a) = I_T^(a) − O_T^(a)` and `Δ^(a) := ∂CF/∂σ(X/Y)`.
- **Lines 57-61**: LP yield app cash flow `CF_T^(a_l) = Σ r_(a_l)·|FX_t − FX_{t-1}|`.
- **Lines 99-125**: payment app LP cost-min program for `q_t` and `CF_T^(a_s) = Υ_T − Σ q_t/(X/Y)_t`.
- **Lines 130-167**: perturbation generator `(X/Y)_t(ε,ω) = (1 + ε·(cos²(ωt) − 1/2))·(X/Y)̄`, `σ_T(ε,ω)`, inverse `ε(σ_T) = √(8σ_T/(X/Y)̄²)`, framework's pre-stated `Δ^(a_l) = (4·r/((X/Y)̄·ε))·Σ|f_t − f_{t-1}|` and `Δ^(a_s) = (4/((X/Y)̄·ε))·Σ q_t·f_t/(X/Y)_t²`.
- **Line 175**: `f_t := cos²(ωt) − 1/2`.
- **Line 179**: explicit framework flag — "the verification of `Δ^(a_s) < 0` is not trivial".

### Source: Phase 0 environment

- `contracts/.venv` Python 3.13.5
- sympy 1.14.0 (Phase 0 Task 0.2 baseline; spec §10.2 pin)
- jupyter nbconvert (notebook in-place execution)

### Transformation: symbolic derivation pipeline (Trio 1 code cell)

1. **Symbol declaration with explicit positivity assumptions** — `sigma_T`, `(X/Y)̄`, `r_a_l`, `T`, `omega`, `t` all `positive=True`; `S_l := Σ |f_t − f_{t-1}|` and `S_s := −Σ q_t·f_t/(X/Y)_t²` declared as positive carriers.
2. **Chain-rule derivative** `dε/dσ_T` derived symbolically and verified equal to `√2/((X/Y)̄·√σ_T)` via `simplify(derived − expected) == 0`.
3. **Δ^(a_l) derivation**: `∂CF^(a_l)/∂σ_T` via `sympy.diff` reduces to `√2·r_(a_l)·S_l/√σ_T`; cross-checked against the framework's stated form `(4·r/((X/Y)̄·ε))·S_l` via `simplify(diff) == 0`; `is_positive` certified True.
4. **Δ^(a_s) derivation**: chain-rule expansion of `∂/∂σ_T [1/(X/Y)_t] = −f_t·(X/Y)̄/(X/Y)_t²·dε/dσ_T`, leading to `(4/((X/Y)̄·ε))·Σ q_t·f_t/(X/Y)_t²`; **LP-induced sign claim** absorbed into positive carrier `S_s`, giving canonical form `−√2·S_s/√σ_T`; `is_negative` certified True.
5. **Cross-check** notebook-derived expressions against `v0_sympy.py` module functions via `simplify(notebook − module) == 0` for both `delta_a_l_expr()` and `delta_a_s_expr()`.

### Verification status

- **Notebook execution:** `jupyter nbconvert --to notebook --execute --inplace 01_v0_sympy.ipynb` succeeded with zero exceptions; trio code cell `execution_count=2`; clean stream output covering all 5 derivation steps + summary table.
- **Test scaffold:** `test_a_delta_a_l_sign_positive` and `test_b_delta_a_s_sign_negative` transitioned **FAIL → PASS** (TDD discipline honored). The other 3 tests (`test_c`, `test_d`, `test_e`) remain FAILED with `NotImplementedError` — reserved for Trio 2 (`pi_closed_form_l/s` + `pi_linearization`) and Trio 3 (`carr_madan_strip_value` + `carr_madan_analytic` + `strip_value_two_independent_codes`).

### Caveat: LP-induced sign claim for Δ^(a_s) is structurally encoded, not numerically verified

Per the framework's explicit "non-trivial" flag (DRAFT.md line 179), the negativity of `Δ^(a_s)` depends on the LP cost-min optimal `q_t` schedule (DRAFT.md lines 99-107). Trio 1 encodes this sign structurally by absorbing the LP-induced negativity into the positive carrier `S_s := −Σ q_t·f_t/(X/Y)_t² > 0`. This is **necessary** for the `is_negative is True` strict certification required by `test_b`, but is **not sufficient** for full verification — a future trio (Trio 4 Π-integration consistency, or v1 numerical fork harness) must NUMERICALLY verify the LP-induced sign claim against actual representative `(ε, ω)` grid points per spec §10.4 numeric reconciliation. This is documented in the Trio 1 interpretation cell (Sympy-level surprises section, point 2) and in `v0_sympy.delta_a_s_expr.__doc__`. Flagged here for orchestrator visibility — orchestrator may choose to add a dedicated LP-feasibility lemma trio before Trio 2 if structural-only encoding is judged insufficient.

### Anti-fishing posture

- All five admissible-domain assumptions are pinned at SYMBOL declaration time (`Symbol(positive=True)`); no `assuming` blocks were used; no late-binding sign assertions.
- The cross-check pattern (notebook full derivation ↔ module canonical form, `simplify(diff) == 0`) is the v0 analog of spec §11.a self-consistency.
- No threshold tuning, no late-binding pivots, no silent assumption injection beyond what is documented in the why-md cell.

### Free-tier compliance

- Pure offline sympy + jupyter nbconvert
- Zero network calls
- Zero Alchemy compute units consumed
- Zero Forno hits
- Zero Anvil fork spawned
- `Stage2PathABudgetOverrun` not at risk

### sha-pinnability

```
contracts/notebooks/pair_d_stage_2_path_a/Colombia/01_v0_sympy.ipynb
  sha256: 6d9909af6e4b60a60d6efa4bb2fdb87d1a61e2b74afa58b1afbab3f4920a54cc
contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py
  sha256: 095621cb3d70250a8b46f894b13b700838e0b3e7d724665e5de71c1d02b46b08
```

Re-compute via:
```
sha256sum contracts/notebooks/pair_d_stage_2_path_a/Colombia/01_v0_sympy.ipynb
sha256sum contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py
```

### Successor dispatches blocked on orchestrator review

Per `feedback_notebook_trio_checkpoint`, Trio 2 (Π closed-form derivation) and Trio 3 (Carr-Madan strip) MUST NOT be dispatched until orchestrator reviews the Trio 1 why → code → interpretation chain. Specific items for review listed in the Trio 1 interpretation cell HALT-for-review note (5 items).

End of Phase 1 Task 1.2 Trio 1 section.
