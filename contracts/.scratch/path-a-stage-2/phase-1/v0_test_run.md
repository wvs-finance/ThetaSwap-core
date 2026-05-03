# v0 TDD failing-test run report — Path A Stage-2 Phase 1 Task 1.1

**Captured:** 2026-05-03T02:32:27Z (UTC)
**Executor:** Senior Developer (Phase 1 Task 1.1 dispatch agent)
**Goal per dispatch brief:** confirm `pytest --tb=short` shows all 5 tests
FAILING (not ERROR), where the failure is an explicit, test-author-defined
condition (NotImplementedError raised by the v0 stub).

## Provenance pin

- Test file: `contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py`
  sha256: `9d34098ff3f3ddbdb17f9881734b0b9c7fde78d6b516661a379abd08caea551e`
- Stub module under test: `contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py`
  sha256: `df76e068e12b83ac86fbada4696b246f8b10ac09211c71079975917b2bc94e4a`
- Spec governing tests: `contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-A-fork-simulate-spec.md`
  v1.2.1, sha256 `1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78`
- Plan: `contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-A-fork-simulate-implementation.md`
  sha256 `05f5216faa62b7a3cccb384215d5da007636d87d2b6d9597a21cb42b4860436d`
- Stage-1 PASS verdict (READ-ONLY anchor): `contracts/.scratch/simple-beta-pair-d/results/VERDICT.md`
  sha256 `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf`

## Environment pins

- Python: 3.13.5 (via `contracts/.venv`, activated per `feedback_venv_activation`)
- pytest: 9.0.3
- sympy: 1.14.0
- numpy: 2.4.4
- scipy: 1.17.1
- Plugins active: typeguard 4.5.1, anyio 4.13.0
- rootdir: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev`
- configfile: `pyproject.toml` (workspace pytest config)

## Command executed

```
source contracts/.venv/bin/activate
pytest contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py --tb=short -v
```

## Output (verbatim)

```
============================= test session starts ==============================
platform linux -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0 -- /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
configfile: pyproject.toml
plugins: typeguard-4.5.1, anyio-4.13.0
collecting ... collected 5 items

contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_a_delta_a_l_sign_positive FAILED [ 20%]
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_b_delta_a_s_sign_negative FAILED [ 40%]
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_c_pi_closed_form_equilibrium_k_l_eq_k_s FAILED [ 60%]
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_d_self_consistency_two_independent_codes FAILED [ 80%]
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_e_carr_madan_strip_reconciles_within_truncation_bound FAILED [100%]

=================================== FAILURES ===================================
________________________ test_a_delta_a_l_sign_positive ________________________
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py:96: in test_a_delta_a_l_sign_positive
    expr = v0_sympy.delta_a_l_expr()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py:61: in delta_a_l_expr
    raise NotImplementedError(
E   NotImplementedError: v0 spec §2(a): symbolic Δ^(a_l) derivation not yet implemented (Phase 1 Task 1.2 trio-3 will land this)
________________________ test_b_delta_a_s_sign_negative ________________________
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py:139: in test_b_delta_a_s_sign_negative
    expr = v0_sympy.delta_a_s_expr()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py:77: in delta_a_s_expr
    raise NotImplementedError(
E   NotImplementedError: v0 spec §2(b): symbolic Δ^(a_s) derivation not yet implemented (Phase 1 Task 1.2 trio-3 will land this; sign verification non-trivial)
_________________ test_c_pi_closed_form_equilibrium_k_l_eq_k_s _________________
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py:181: in test_c_pi_closed_form_equilibrium_k_l_eq_k_s
    pi_l = v0_sympy.pi_closed_form_l(sigma_T_sym, K_l_sym)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py:89: in pi_closed_form_l
    raise NotImplementedError(
E   NotImplementedError: v0 spec §2(c): Π^l closed-form not yet implemented (Phase 1 Task 1.3 trio-4 will land this)
________________ test_d_self_consistency_two_independent_codes _________________
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py:239: in test_d_self_consistency_two_independent_codes
    impl_a, impl_b = v0_sympy.strip_value_two_independent_codes(
contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py:170: in strip_value_two_independent_codes
    raise NotImplementedError(
E   NotImplementedError: v0 spec §11.a: two-code self-consistency not yet implemented (Phase 1 Task 1.3 trio-6 will land this)
__________ test_e_carr_madan_strip_reconciles_within_truncation_bound __________
contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py:272: in test_e_carr_madan_strip_reconciles_within_truncation_bound
    strip_value, leg_breakdown = v0_sympy.carr_madan_strip_value(
contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py:137: in carr_madan_strip_value
    raise NotImplementedError(
E   NotImplementedError: v0 spec §2(e) + §10.5: Carr-Madan strip not yet implemented (Phase 1 Task 1.3 trio-5 will land this)
=========================== short test summary info ============================
FAILED contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_a_delta_a_l_sign_positive
FAILED contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_b_delta_a_s_sign_negative
FAILED contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_c_pi_closed_form_equilibrium_k_l_eq_k_s
FAILED contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_d_self_consistency_two_independent_codes
FAILED contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py::test_e_carr_madan_strip_reconciles_within_truncation_bound
============================== 5 failed in 0.24s ===============================
```

Process exit code: `1` (5 of 5 tests failed; pytest standard exit code for any
test failure).

## Failure-mode classification

Per `feedback_strict_tdd`, the load-bearing distinction is FAILED vs ERROR:

- **FAILED** = the test ran to completion and the assertion did not hold
  (or, equivalently, an exception bubbled up from inside the test body that
  the test author authored as the failure path). This is the desired TDD
  state: the test is meaningful, it executes the API surface, and it surfaces
  the missing implementation as a single-line message tied to a spec sub-
  criterion.
- **ERROR** = the test could not be collected, or an unrelated framework
  error (import failure, fixture error, syntax error, etc.) prevented the
  test body from even running. This would mean the scaffold is broken and
  not actually testing the spec.

All 5 tests show `FAILED` (top of summary), traced back to specific lines in
the test body that intentionally invoke the stub API. The stub raises
`NotImplementedError` — a normal Python exception that pytest correctly
classifies as a test failure (not a collection error, not a fixture error).
This satisfies the dispatch brief's requirement of "5 FAILED (not 5 ERROR)".

## Mapping of 5 tests → 5 dispatch-brief criteria

| Dispatch-brief test # | Pytest test name | Spec §2 v0 sub-criterion | First failure stub |
|---|---|---|---|
| 1 (Δ^(a_l) > 0) | `test_a_delta_a_l_sign_positive` | §2 v0 (a) | `delta_a_l_expr()` |
| 2 (Δ^(a_s) < 0) | `test_b_delta_a_s_sign_negative` | §2 v0 (b) | `delta_a_s_expr()` |
| 3 (Π closed form K_l = K_s) | `test_c_pi_closed_form_equilibrium_k_l_eq_k_s` | §2 v0 (c) + framework line 227 | `pi_closed_form_l(...)` |
| 4 (Carr-Madan vs analytic per §11.b) | `test_e_carr_madan_strip_reconciles_within_truncation_bound` | §2 v0 (e) + §11.b | `carr_madan_strip_value(...)` |
| 5 (Self-consistency per §11.a) | `test_d_self_consistency_two_independent_codes` | §11.a | `strip_value_two_independent_codes(...)` |

Test naming convention `test_{a,b,c,d,e}_*` follows alphabetical letter
mapping to spec §2 v0 sub-criteria (a)-(e); pytest collection order is
alphabetical so the order of execution in the run output is `a → b → c → d → e`.
Note: dispatch-brief test #4 maps to pytest test `e` (Carr-Madan vs analytic
per §11.b), and dispatch-brief test #5 maps to pytest test `d` (§11.a self-
consistency); the cross-mapping is recorded in the test module docstring.

## Phase 1 Task 1.2 + 1.3 + 1.4 → PASS conversion path

Per plan §3 Phase 1 Task 1.2 + 1.3 + 1.4, the trio-checkpoint Analytics
Reporter dispatch implements the v0 sympy ladder across three notebooks.
Each notebook trio retires one or more stub `NotImplementedError`s, turning
the corresponding test's `FAILED` into `PASS`:

- **Task 1.2 / NB-01 trio 1-3 → tests a + b PASS**
  - Trio 3 lands `delta_a_l_expr()` and `delta_a_s_expr()` symbolic
    derivations under the framework's positive-q_t admissible domain.
- **Task 1.3 / NB-02 trio 4-6 → tests c + d + e PASS**
  - Trio 4 lands `pi_closed_form_l()`, `pi_closed_form_s()`, and
    `pi_linearization()` (closed forms K_l·√σ_T, K_s·√σ_T, K̂·σ_T).
  - Trio 5 lands `carr_madan_strip_value()` and `carr_madan_analytic()`
    (3 condors × 4 legs = 12 legs per spec §10.5; weights ∝ 1/K²).
  - Trio 6 lands `strip_value_two_independent_codes()` (§11.a self-
    consistency check, two independent codings agreeing at ≤1.2e-9).
- **Task 1.4 / NB-03** synthesizes the exit report; no new stub
  implementations needed for the test suite to PASS.

After Task 1.4 lands, this same `pytest --tb=short -v` invocation should
return `5 passed` and the Phase 1 Gate B1 review (Task 1.5, 3-way
Code Reviewer + Reality Checker + Senior Developer) is dispatched.

## Caveats / surprises

1. **Pre-existing v0_sympy.py stub.** The file
   `contracts/.scratch/path-a-stage-2/phase-1/v0_sympy.py` was authored
   alongside this dispatch's pre-flight (untracked at dispatch start). Its
   API surface mirrors the framework note's symbolic claims and provides
   `NotImplementedError`-raising stubs aligned exactly with the 5 spec §2 v0
   sub-criteria. The TDD scaffold was authored against this stub's API
   surface so the failing-test discipline holds end-to-end: tests collect
   cleanly (no import errors), invoke the stub, and fail at the
   `NotImplementedError`. This is the canonical TDD scaffold pattern; the
   stub is not an "implementation" — it is the seam against which the
   real notebook-trio implementations will be hung in Tasks 1.2 + 1.3.

2. **Test path: dispatch-brief vs plan §3 mismatch.** The dispatch brief
   instructs `contracts/.scratch/path-a-stage-2/phase-1/test_v0_exit_criteria.py`;
   the plan §3 Phase 1 Task 1.1 instructs
   `contracts/.scratch/pair-d-stage-2-path-a/tests/test_v0_exit_criteria.py`.
   The dispatch brief is the authoritative input for THIS execution per the
   "INPUTS" section header; honored as such. No file is created at the plan-
   path location; if Phase 5 audit (Task 5.1, Reality Checker) flags this as
   a path-conflict between plan and brief, a follow-up CORRECTIONS-block
   should harmonize the two — that is out of scope for Task 1.1.

3. **No notebooks touched.** Task 1.1 is a pure-Python pytest scaffold,
   NOT a notebook authoring task. Notebooks
   `01_v0_sympy.ipynb`, `02_v1_mento_fork.ipynb`, etc. (Task 0.2 outputs
   under `contracts/notebooks/pair_d_stage_2_path_a/Colombia/`) are
   unmodified. The trio-checkpoint discipline (`feedback_notebook_trio_checkpoint`)
   applies to Tasks 1.2 + 1.3 + 1.4 (Analytics Reporter dispatch), not Task 1.1.

4. **Free-tier compliance.** Pure offline sympy + pytest invocation; no
   network calls; no Alchemy CU consumption; no Forno hits; no Anvil fork
   spawned. `Stage2PathABudgetOverrun` not at risk.

5. **Dependency drift verification.** The only Phase-1 dependencies
   actually consumed are sympy 1.14.0 + numpy 2.4.4 + pytest 9.0.3 (all
   pinned via `contracts/notebooks/pair_d_stage_2_path_a/Colombia/requirements.txt`
   and verified at Phase 0 Task 0.2 commit). No new dependency added.

6. **Sympy `is_positive` / `is_negative` semantics.** The (a) and (b)
   tests rely on sympy's tri-state Boolean (`True` / `False` / `None`).
   For Tasks 1.2 + 1.3 to PASS test (a), the implementation must produce
   an expression where `simplify(expr).is_positive is True` (i.e., `None`
   is treated as a FAIL, which forces the trio-3 author to encode the
   admissible-domain assumptions explicitly via sympy `Symbol(positive=True)`
   declarations or equivalent). This is intentional anti-fishing discipline:
   the framework note line 179 explicitly flags Δ^(a_s) sign verification
   as non-trivial; relying on `is_negative is None` would silently elide
   that non-triviality. The trio author must justify the sign claim to the
   sympy engine, not to the test runner.

7. **No HALT triggered.** No typed exception fired during this dispatch.
   The work product is a clean TDD scaffold ready for Phase 1 Task 1.2
   dispatch.
