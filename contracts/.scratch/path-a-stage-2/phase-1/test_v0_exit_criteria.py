"""TDD failing-test scaffold for Pair D Stage-2 Path A v0 exit criteria.

Per `feedback_strict_tdd` (NON-NEGOTIABLE): this test module is authored BEFORE
any v0 sympy implementation lands. The 5 tests below encode spec §2 v0
sub-criteria (a)-(e) verbatim and must FAIL on first run because
`v0_sympy.py` is a stub raising NotImplementedError. Phase 1 Task 1.2 + 1.3 +
1.4 (Analytics Reporter, trio-checkpoint discipline) implement the v0 ladder
across three notebooks; trio-3 (Carr-Madan strip reconciliation) lands the
final implementation that turns these 5 FAILs into 5 PASSes.

Spec governing tests: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-A-fork-simulate-spec.md
  v1.2.1 sha256 1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78

Plan governing tests: contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-A-fork-simulate-implementation.md
  sha256 05f5216faa62b7a3cccb384215d5da007636d87d2b6d9597a21cb42b4860436d

CPO framework imported derivation: contracts/notes/2026-04-29-macro-markets-draft-import.md
  Lines 130-272: (X/Y)_t(ε,ω) → σ_T(ε,ω) → ε(σ_T) → Δ^(a_l), Δ^(a_s) →
  Π = K·√σ_T → linearization Π ≈ K̂·σ_T → Carr-Madan log-contract identity →
  3-condor / 12-leg discrete strip approximation.

Stage-1 PASS verdict (READ-ONLY anchor; NOT re-tested here):
  contracts/.scratch/simple-beta-pair-d/results/VERDICT.md
  sha256 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf

Test naming convention:
  test_a_*  — spec §2 v0 (a): Δ^(a_l) > 0
  test_b_*  — spec §2 v0 (b): Δ^(a_s) < 0
  test_c_*  — spec §2 v0 (c): Π(σ_T) closed form K_l = K_s
  test_d_*  — implicit in (e); explicit two-impl self-consistency per §11.a
  test_e_*  — spec §2 v0 (e): Carr-Madan strip vs analytic per §11.b

Five-test mapping (per dispatch brief):
  test 1 ↔ test_a_delta_a_l_sign_positive
  test 2 ↔ test_b_delta_a_s_sign_negative
  test 3 ↔ test_c_pi_closed_form_equilibrium_k_l_eq_k_s
  test 4 ↔ test_e_carr_madan_strip_reconciles_within_truncation_bound
  test 5 ↔ test_d_self_consistency_two_independent_codes
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add the phase-1/ directory to sys.path so the v0_sympy stub is importable.
# The stub raises NotImplementedError on every API call, which is exactly
# what TDD requires: the tests collect cleanly but fail loudly until Phase 1
# Tasks 1.2-1.4 land the real implementation.
_HERE: Path = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import v0_sympy  # noqa: E402  (intentional post-sys.path mutation)


# ── Spec-pinned numerical constants (mirrored from env.py / spec §10.5 + §11) ─

# §10.5: 3 IronCondor positions × 4 legs each = 12 legs total
N_LEGS: int = 12
N_CONDORS: int = 3
LEGS_PER_POSITION: int = 4

# §11.a: self-consistency tolerance (machine-epsilon × N_legs)
SELF_CONSISTENCY_TOL: float = 1e-10 * N_LEGS  # 1.2e-9 absolute per payoff eval

# §11.b: truncation/discretization bound (analytic-vs-strip), 5% relative
TRUNCATION_BOUND_REL: float = 5.0e-2

# §11.b baseline: GBM σ_0 = 10% representative of pinned COP/USD historical range
GBM_SIGMA_0_BASELINE: float = 0.10

# Reference spot for Carr-Madan reconciliation (notional units; relative metric)
S_0_BASELINE: float = 1.0


# ── Spec §2 v0 (a): Δ^(a_l) > 0 ─────────────────────────────────────────────


def test_a_delta_a_l_sign_positive() -> None:
    """spec §2 v0 (a): Δ^(a_l) > 0 over admissible 0 < ε < 1.

    Framework note line 165:
        Δ^(a_l) = (4·r_(a_l) / ((X/Y)̄·ε(σ_T))) · Σ_t |f_t − f_{t−1}| > 0

    The sign claim follows trivially from positivity of r_(a_l), (X/Y)̄,
    ε(σ_T) (since ε(σ_T) = √(8·σ_T/(X/Y)̄²) ≥ 0), and absolute-value sum
    of f_t increments. Task 1.2 (Analytics Reporter, trio 3) must produce
    a sympy expression whose `.is_positive` is True or whose simplified
    form is manifestly positive over the admissible domain.

    FAILURE MODE: this test FAILS until v0_sympy.delta_a_l_expr() returns
    a sympy expression instead of raising NotImplementedError.
    """
    expr = v0_sympy.delta_a_l_expr()
    # Guard: returned object must be a sympy expression (not None/dict/etc).
    import sympy

    assert isinstance(expr, sympy.Expr), (
        "spec §2 v0 (a): delta_a_l_expr() must return a sympy.Expr; "
        f"got {type(expr).__name__}"
    )
    # Sign claim: the expression must simplify to something the symbolic
    # engine can certify as positive (or at least non-negative with
    # explicit zero-point characterization). Task 1.2 trio-3 chooses the
    # exact admissible-domain assumption set; for the test the strict
    # positive certification is the load-bearing claim.
    is_pos = sympy.simplify(expr).is_positive
    assert is_pos is True, (
        "spec §2 v0 (a): Δ^(a_l) sign claim FAILED. "
        f"Expected sympy.simplify(expr).is_positive == True; got {is_pos!r}. "
        "Framework note line 165 requires Δ^(a_l) > 0 strictly over admissible "
        "0 < ε < 1; Task 1.2 must produce a derivation whose admissible-domain "
        "assumptions certify strict positivity."
    )


# ── Spec §2 v0 (b): Δ^(a_s) < 0 ─────────────────────────────────────────────


def test_b_delta_a_s_sign_negative() -> None:
    """spec §2 v0 (b): Δ^(a_s) < 0 over admissible 0 < ε < 1.

    Framework note lines 167 + 179 (explicit non-trivial flag):
        Δ^(a_s) = -(4 / ((X/Y)̄·ε(σ_T))) · Σ_t q_t·f_t/(X/Y)_t² < 0
        Note: The verification of Δ^(a_s) < 0 is not trivial.

    The sign claim depends on q_t > 0 (LP constraint, framework lines 99-107)
    AND on the structural claim that the q_t-weighted sum of f_t/(X/Y)_t²
    aligns with the leading minus sign. Task 1.2 (trio 3) must justify the
    sign claim symbolically over the admissible domain — auto-asserting
    `is_negative` without the q_t-weighted argument is anti-fishing-banned
    per `feedback_pathological_halt_anti_fishing_checkpoint`.

    FAILURE MODE: this test FAILS until v0_sympy.delta_a_s_expr() returns
    a sympy expression instead of raising NotImplementedError.
    """
    expr = v0_sympy.delta_a_s_expr()
    import sympy

    assert isinstance(expr, sympy.Expr), (
        "spec §2 v0 (b): delta_a_s_expr() must return a sympy.Expr; "
        f"got {type(expr).__name__}"
    )
    is_neg = sympy.simplify(expr).is_negative
    assert is_neg is True, (
        "spec §2 v0 (b): Δ^(a_s) sign claim FAILED. "
        f"Expected sympy.simplify(expr).is_negative == True; got {is_neg!r}. "
        "Framework note line 167 requires Δ^(a_s) < 0 strictly; line 179 flags "
        "this as non-trivial and demands a q_t-weighted symbolic justification. "
        "Task 1.2 trio-3 must land the certified-negative form."
    )


# ── Spec §2 v0 (c): Π(σ_T) closed form satisfies equilibrium K_l = K_s ──────


def test_c_pi_closed_form_equilibrium_k_l_eq_k_s() -> None:
    """spec §2 v0 (c): Π(σ_T) = K·√σ_T closed form on both sides; K_l = K_s.

    Framework note lines 209-227:
        Π^l(σ_T) = -∫₀^σ_T Δ^(a_l)(u) du = K_l·√σ_T   (lines 209-216)
        Π^s(σ_T) = K_s·√σ_T                            (lines 222-225)
        Equilibrium iff K_s = K_l                       (line 227)

    The test asserts: (i) both closed forms are sympy expressions of the
    form `K · sqrt(sigma_T)` for some constant K; (ii) the equilibrium
    condition K_l = K_s yields algebraically equal expressions when the
    K_l, K_s symbols are unified.

    FAILURE MODE: this test FAILS until v0_sympy.pi_closed_form_l() and
    v0_sympy.pi_closed_form_s() return real sympy expressions instead of
    raising NotImplementedError.
    """
    import sympy

    sigma_T_sym = sympy.symbols("sigma_T", positive=True)
    K_l_sym, K_s_sym = sympy.symbols("K_l K_s", real=True)

    pi_l = v0_sympy.pi_closed_form_l(sigma_T_sym, K_l_sym)
    pi_s = v0_sympy.pi_closed_form_s(sigma_T_sym, K_s_sym)

    assert isinstance(pi_l, sympy.Expr), (
        "spec §2 v0 (c): pi_closed_form_l(...) must return a sympy.Expr; "
        f"got {type(pi_l).__name__}"
    )
    assert isinstance(pi_s, sympy.Expr), (
        "spec §2 v0 (c): pi_closed_form_s(...) must return a sympy.Expr; "
        f"got {type(pi_s).__name__}"
    )

    # Structural form: Π^l should equal K_l·√σ_T exactly.
    expected_l = K_l_sym * sympy.sqrt(sigma_T_sym)
    expected_s = K_s_sym * sympy.sqrt(sigma_T_sym)
    diff_l = sympy.simplify(pi_l - expected_l)
    diff_s = sympy.simplify(pi_s - expected_s)
    assert diff_l == 0, (
        f"spec §2 v0 (c): Π^l(σ_T) closed form MISMATCH. "
        f"Expected K_l·√σ_T; got {pi_l}; diff = {diff_l}. "
        "Framework note lines 209-216 require this exact closed form."
    )
    assert diff_s == 0, (
        f"spec §2 v0 (c): Π^s(σ_T) closed form MISMATCH. "
        f"Expected K_s·√σ_T; got {pi_s}; diff = {diff_s}. "
        "Framework note lines 222-225 require this exact closed form."
    )

    # Equilibrium check: substituting K_s ← K_l yields algebraically equal forms.
    K_unified = sympy.symbols("K", real=True)
    pi_l_unified = pi_l.subs(K_l_sym, K_unified)
    pi_s_unified = pi_s.subs(K_s_sym, K_unified)
    diff_eq = sympy.simplify(pi_l_unified - pi_s_unified)
    assert diff_eq == 0, (
        "spec §2 v0 (c): equilibrium K_l = K_s does not yield algebraically "
        f"equal Π^l and Π^s. Difference after substitution: {diff_eq}. "
        "Framework note line 227 requires equilibrium iff K_l = K_s."
    )


# ── Spec §11.a: self-consistency check (deterministic, code-vs-code) ────────


def test_d_self_consistency_two_independent_codes() -> None:
    """spec §11.a: two independent codings of the strip value agree at
    ≤ 1e-10 × N_legs absolute error per payoff evaluation.

    Per spec §11.a, this metric distinguishes a CODE bug (triage:
    debugger / unit test) from a MODEL bug (triage: spec amendment). Two
    implementations of the IronCondor strip (e.g., explicit per-leg
    summation vs sympy-derived closed-form payoff function) must agree at
    machine-epsilon × N_legs scale. With N_legs = 12, the absolute
    tolerance is 1.2e-9.

    FAILURE MODE: this test FAILS until v0_sympy.strip_value_two_independent_codes()
    returns a (impl_a_value, impl_b_value) tuple instead of raising
    NotImplementedError.
    """
    impl_a, impl_b = v0_sympy.strip_value_two_independent_codes(
        S_0=S_0_BASELINE,
        sigma_0=GBM_SIGMA_0_BASELINE,
        n_condors=N_CONDORS,
        legs_per_condor=LEGS_PER_POSITION,
    )
    abs_diff = abs(impl_a - impl_b)
    assert abs_diff <= SELF_CONSISTENCY_TOL, (
        f"spec §11.a: code-vs-code self-consistency FAILED. "
        f"|impl_a - impl_b| = {abs_diff:.3e} exceeds tolerance "
        f"{SELF_CONSISTENCY_TOL:.3e} (1e-10 × N_legs = 1e-10 × {N_LEGS}). "
        "Per spec §11.a failure mode: this is a code-bug, not a model-bug; "
        "triage path is debugger/unit-test, NOT spec amendment."
    )


# ── Spec §11.b + §2 v0 (e): Carr-Madan strip reconciles within truncation bound ─


def test_e_carr_madan_strip_reconciles_within_truncation_bound() -> None:
    """spec §2 v0 (e) + §11.b: Carr-Madan 12-leg strip reconciles to analytic
    Π within the §11.b truncation/discretization bound.

    Spec §11.b pre-commits a 5e-2 (5%) relative-error threshold for the
    v0 / v2 strip-vs-analytic reconciliation under the §10.5 strike grid
    (3 condors × 4 legs at K_j ≈ S_0·exp(x_j), w_j ∝ 1/K_j², x_j uniform
    on [-x_max, +x_max] with x_max ≈ 3·σ_0). Under GBM σ_0 = 10% baseline,
    the closed-form ε_total ≈ O(1e-2) at this grid resolution.

    FAILURE MODE: this test FAILS until v0_sympy.carr_madan_strip_value()
    and v0_sympy.carr_madan_analytic() return real numerical values instead
    of raising NotImplementedError.
    """
    strip_value, leg_breakdown = v0_sympy.carr_madan_strip_value(
        S_0=S_0_BASELINE,
        sigma_0=GBM_SIGMA_0_BASELINE,
        n_condors=N_CONDORS,
        legs_per_condor=LEGS_PER_POSITION,
    )
    analytic_value = v0_sympy.carr_madan_analytic(
        S_0=S_0_BASELINE,
        sigma_0=GBM_SIGMA_0_BASELINE,
    )

    # Structural guard: leg breakdown must enumerate exactly N_legs entries
    # (per spec §10.5), each carrying (strike, weight, payoff_contribution)
    # so the §11.a self-consistency test can cross-reference.
    assert len(leg_breakdown) == N_LEGS, (
        f"spec §10.5: leg breakdown must enumerate exactly {N_LEGS} legs "
        f"({N_CONDORS} condors × {LEGS_PER_POSITION} legs); got "
        f"{len(leg_breakdown)} legs."
    )

    # Reconciliation check: relative error against analytic must be within
    # the §11.b 5% truncation bound at the §10.5 grid + GBM σ_0 = 10% baseline.
    if analytic_value == 0:
        # Pathological zero-analytic case — would require careful absolute
        # tolerance handling; spec §11.b is relative-error-based so we
        # assert non-zero analytic explicitly.
        pytest.fail(
            "spec §11.b: analytic Carr-Madan value is zero — the §11.b "
            "relative-error metric is undefined; check carr_madan_analytic() "
            "implementation."
        )
    rel_err = abs(strip_value - analytic_value) / abs(analytic_value)
    assert rel_err <= TRUNCATION_BOUND_REL, (
        f"spec §11.b + §2 v0 (e): Carr-Madan strip reconciliation FAILED. "
        f"|strip - analytic| / |analytic| = {rel_err:.3e} "
        f"exceeds {TRUNCATION_BOUND_REL:.3e} (5% relative bound at §10.5 "
        f"grid + GBM σ_0 = {GBM_SIGMA_0_BASELINE}). Per spec §11.b failure "
        f"mode at baseline grid + baseline σ_0: this triggers "
        "`Stage2PathAFrameworkInternallyInconsistent` (v0 typed exception), "
        "NOT silent threshold tuning."
    )
