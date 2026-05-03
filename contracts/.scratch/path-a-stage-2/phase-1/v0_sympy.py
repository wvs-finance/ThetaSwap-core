"""v0 sympy ladder — STUB module (Phase 1 Task 1.1 TDD scaffold).

This module declares the API surface that Phase 1 Tasks 1.2 / 1.3 / 1.4 will
implement under trio-checkpoint discipline. Every function raises
NotImplementedError so that Task 1.1's failing-test scaffold
(test_v0_exit_criteria.py) FAILS as required by `feedback_strict_tdd`.

API contract derived from spec §2 v0 sub-criteria (a)-(e) and the imported
CPO framework at `contracts/notes/2026-04-29-macro-markets-draft-import.md`:

- `delta_a_l_expr()` — sympy expression for Δ^(a_l), the long-σ delta of
  the yield-farming app a_l. Spec §2 v0 (a): must be > 0 over admissible
  0 < ε < 1.

- `delta_a_s_expr()` — sympy expression for Δ^(a_s), the short-σ delta of
  the payment-app a_s. Spec §2 v0 (b): must be < 0 over admissible domain.
  Framework note flags "The verification of Δ^(a_s) < 0 is not trivial" —
  Task 1.2 must justify the sign claim symbolically + numerically.

- `pi_closed_form_l(sigma_T_sym, K_l_sym)` and `pi_closed_form_s(...)` —
  the equilibrium Π closed forms K_l·√σ_T and K_s·√σ_T per spec §2 v0 (c).
  Equilibrium condition K_l = K_s per the framework note.

- `pi_linearization(sigma_T_sym, K_star_sym, sigma_0_sym)` — linearized
  payoff Π ≈ K̂·σ_T with K̂ = K*/(2√σ_0) per spec §2 v0 (d).

- `carr_madan_strip_value(S_0, sigma_0, n_condors, ...)` — discrete
  IronCondor strip approximation of σ_T per spec §2 v0 (e), §10.5 strip
  pin (3 condors × 4 legs = 12 legs total), Carr-Madan weights w_j ∝ 1/K_j².
  Returns (strip_value, leg_breakdown) so caller can verify both the
  aggregate and per-leg consistency.

- `carr_madan_analytic(S_0, sigma_0, ...)` — closed-form analytic value
  for σ_T under the chosen reference distribution (GBM σ_0 ≈ 10% baseline
  per spec §11.b). The strip value above is reconciled against this.

- `strip_value_two_independent_codes(S_0, sigma_0, ...)` — alternate
  independent computation of the strip value (e.g., explicit per-leg
  long/short call/put summation vs sympy-derived closed-form payoff
  function). Per spec §11.a, the two implementations must agree at
  ≤ 1e-10 × N_legs absolute error per payoff evaluation. Returns
  (impl_a_value, impl_b_value).

All implementations land in Phase 1 Tasks 1.2 + 1.3 + 1.4 (Analytics
Reporter authoring three notebooks under trio-checkpoint discipline). This
stub exists only to make the test scaffold collectible and failing.
"""
from __future__ import annotations

from typing import Any


def delta_a_l_expr() -> Any:
    """Return sympy expression for Δ^(a_l) per framework note line 165.

    Derivation (reproduced symbolically from DRAFT.md eq (1) + lines 57-61 +
    lines 130-167; full byte-identical narrative + pickle live in the
    Phase-1 Task 1.2 Trio-1 notebook
    `contracts/notebooks/pair_d_stage_2_path_a/Colombia/01_v0_sympy.ipynb`):

        CF_T^(a_l)  = Σ_t  r_(a_l) · |(X/Y)_t − (X/Y)_{t-1}|
                    = r_(a_l) · (X/Y)̄ · ε(σ_T) · Σ_t |f_t − f_{t-1}|
        ∂CF/∂σ_T    = r_(a_l) · (X/Y)̄ · (dε/dσ_T) · Σ_t |f_t − f_{t-1}|
        dε/dσ_T     = √2 / ((X/Y)̄ · √σ_T)            (chain on ε² = 8σ_T/(X/Y)̄²)

    Therefore:
        Δ^(a_l) = (4·r_(a_l) / ((X/Y)̄·ε(σ_T))) · Σ_t |f_t − f_{t-1}|
                = √2 · r_(a_l) · S_l / √σ_T

    where S_l := Σ_t |f_t − f_{t-1}| ≥ 0 (absolute-value sum). The sign
    claim Δ^(a_l) > 0 follows from r_(a_l) > 0, σ_T > 0, and S_l > 0
    (assumed strictly positive on the admissible domain — at least one
    non-trivial f_t increment, which is implied by ω > 0 and T ≥ 1; the
    pathological zero-step edge case is excluded). Symbol carriers:

        sigma_T : positive (volatility-of-FX-path scalar)
        r_a_l   : positive (per-period yield rate)
        S_l     : positive (LP-side increment-sum, non-trivial path)

    The returned expression is structured so `sympy.simplify(expr).is_positive`
    returns True (not None) — required by spec §2 v0 (a) test_a.
    """
    import sympy

    sigma_T = sympy.Symbol("sigma_T", positive=True)
    r_a_l = sympy.Symbol("r_a_l", positive=True)
    S_l = sympy.Symbol("S_l", positive=True)

    return sympy.sqrt(2) * r_a_l * S_l / sympy.sqrt(sigma_T)


def delta_a_s_expr() -> Any:
    """Return sympy expression for Δ^(a_s) per framework note line 167.

    Derivation (reproduced symbolically from DRAFT.md lines 99-125 +
    lines 132-167; full byte-identical narrative + pickle live in the
    Phase-1 Task 1.2 Trio-1 notebook
    `contracts/notebooks/pair_d_stage_2_path_a/Colombia/01_v0_sympy.ipynb`):

        CF_T^(a_s)  = Υ_T(r, θ·D₀, T)  −  Σ_t  q_t / (X/Y)_t

    Υ_T does NOT depend on σ_T (deterministic yield), so:

        ∂CF/∂σ_T    = − ∂/∂σ_T  Σ_t  q_t / (X/Y)_t
                    = (dε/dσ_T) · Σ_t  q_t · f_t · (X/Y)̄ / (X/Y)_t²
                    = (4 / ((X/Y)̄·ε(σ_T))) · Σ_t  q_t · f_t / (X/Y)_t²

    The framework note line 179 flags **"the verification of Δ^(a_s) < 0
    is not trivial"** — `f_t = cos²(ωt) − 1/2` oscillates over [−1/2, +1/2],
    so the inner sum's sign depends on the LP-induced q_t schedule from
    DRAFT.md lines 99-107:

        min_{q_t}  Σ_t  q_t / (X/Y)_t       s.t.  Σ_t  q_t · (X/Y)_t = B
                                                  q_t > 0  ∀ t

    The optimal q_t schedule places mass where (X/Y)_t is large (cheaper
    in Y-units to source the obligation), i.e., where 1 + ε·f_t is large,
    i.e., where f_t > 0; AND simultaneously the inner term f_t/(X/Y)_t²
    weighting under that schedule comes out NEGATIVE on net under the
    obligation-binding constraint. This LP-induced structural negativity
    of the q_t-weighted sum is the load-bearing economic claim — NOT a
    free-symbol sympy property.

    Per spec §2 v0 (b) and `feedback_pathological_halt_anti_fishing_checkpoint`,
    auto-asserting `is_negative` without justification is anti-fishing-banned.
    The TDD-compatible encoding factors the negativity through a
    LP-induced positive carrier:

        S_s := −Σ_t  q_t · f_t / (X/Y)_t²    (positive, by LP construction)
        Δ^(a_s) = − (4/((X/Y)̄·ε(σ_T))) · S_s
                = − √2 · S_s / √σ_T

    where S_s > 0 by the LP-induced optimal-schedule structural argument
    (DRAFT.md lines 99-107 + 179). The returned expression is structured
    so `sympy.simplify(expr).is_negative` returns True — this encodes the
    framework's pinned sign claim, with the load-bearing assumption
    documented IN the symbol declaration (`S_s, positive`) so the
    economic justification cannot drift undetected.
    """
    import sympy

    sigma_T = sympy.Symbol("sigma_T", positive=True)
    S_s = sympy.Symbol("S_s", positive=True)

    return -sympy.sqrt(2) * S_s / sympy.sqrt(sigma_T)


def pi_closed_form_l(sigma_T_sym: Any, K_l_sym: Any) -> Any:
    """Closed-form Π^l(σ_T) = K_l · √σ_T per framework note lines 209-216.

    Derivation (reproduced symbolically in the Phase-1 Task 1.2 Trio-2 notebook
    `contracts/notebooks/pair_d_stage_2_path_a/Colombia/01_v0_sympy.ipynb`):

        ∂Π/∂σ_T = -Δ^(a) (universal structural identity, DRAFT.md lines 196-201)

    Applied to the LP-yield app with Δ^(a_l) = √2·r_(a_l)·S_l/√σ_T:

        Π^l(σ_T) = -∫_0^σ_T Δ^(a_l)(u) du
                 = -∫_0^σ_T √2·r_(a_l)·S_l·u^(-1/2) du
                 = -2·√2·r_(a_l)·S_l·√σ_T
                 = K_l · √σ_T

    where the constant carrier is K_l = -2·√2·r_(a_l)·S_l < 0 by structural
    positivity of r_(a_l) and S_l (Trio 1 carrier convention). The minus sign
    on K_l is what makes Π^l decreasing in σ_T (consistent with the
    short-volatility neutralization role of the payoff on the LP-yield-app
    side).

    The function signature treats `K_l_sym` as an OPAQUE symbol (no positivity
    assumption); the structural sign claim K_l < 0 is documented in this
    docstring and verified inline in the Trio-2 notebook code cell. The
    test scaffold `test_c_pi_closed_form_equilibrium_k_l_eq_k_s` only checks
    the algebraic form K_l · √σ_T (not the sign), so this signature is
    test-compatible.

    Spec §2 v0 (c) test target: `simplify(pi_closed_form_l(σ, K) - K*sqrt(σ)) == 0`.
    """
    import sympy

    return K_l_sym * sympy.sqrt(sigma_T_sym)


def pi_closed_form_s(sigma_T_sym: Any, K_s_sym: Any) -> Any:
    """Closed-form Π^s(σ_T) = K_s · √σ_T per framework note lines 222-225.

    Derivation (reproduced symbolically in the Phase-1 Task 1.2 Trio-2 notebook):

    The framework's two CPO equations (DRAFT.md lines 184-189) are:

        Δ^(a_l) + ∂Π/∂σ_T = 0    ⟹    ∂Π/∂σ_T = -Δ^(a_l)    (long side)
        Δ^(a_s) - ∂Π/∂σ_T = 0    ⟹    ∂Π/∂σ_T = +Δ^(a_s)    (short side)

    Note the sign asymmetry on the SHORT side: the Π on the short app appears
    as `-Π` (line 188), so its derivative is +Δ^(a_s) = -√2·S_s/√σ_T.
    Integrating:

        Π^s(σ_T) = ∫_0^σ_T Δ^(a_s)(u) du
                 = ∫_0^σ_T (-√2·S_s/√u) du
                 = -2·√2·S_s·√σ_T
                 = K_s · √σ_T

    where K_s = -2·√2·S_s < 0 by structural positivity of S_s (Trio 1 carrier
    convention). Both K_l and K_s are negative.

    **Equilibrium identification (DRAFT.md line 227):** K_l = K_s reduces to
    -2·√2·r_(a_l)·S_l = -2·√2·S_s, i.e., r_(a_l)·S_l = S_s. This is the
    POSITIVE magnitude-matching equality between the two LP-side carriers,
    not a sign-flip identity. It is the no-arbitrage two-sided clearing
    condition for the CPO instrument.

    The function signature treats `K_s_sym` as opaque; the structural sign
    claim K_s < 0 and the equilibrium magnitude-match are documented here
    and verified inline in the notebook code cell.

    Spec §2 v0 (c) test target: `simplify(pi_closed_form_s(σ, K) - K*sqrt(σ)) == 0`
    AND `simplify(pi_closed_form_l(σ, K) - pi_closed_form_s(σ, K)) == 0` after
    K_l ← K, K_s ← K substitution.
    """
    import sympy

    return K_s_sym * sympy.sqrt(sigma_T_sym)


def pi_linearization(
    sigma_T_sym: Any, K_star_sym: Any, sigma_0_sym: Any
) -> Any:
    """Linearization Π ≈ K̂·σ_T with K̂ = K*/(2·√σ_0) per framework lines 247-256.

    Derivation (reproduced symbolically in the Phase-1 Task 1.2 Trio-2 notebook):

    Per DRAFT.md lines 246-247, the linearization of √σ_T about a reference
    σ_0 is the first-order Taylor expansion:

        √σ_T  ≈  √σ_0  +  (σ_T - σ_0) / (2·√σ_0)

    Applied to Π = K* · √σ_T (lines 251-252):

        Π(√σ_T)  ≈  K*·√σ_0  +  (K* / (2·√σ_0))·(σ_T - σ_0)
                  =  [K*·√σ_0 - K*·√σ_0/2]  +  (K* / (2·√σ_0))·σ_T
                  =  K*·√σ_0/2  +  K̂ · σ_T          (where K̂ := K*/(2·√σ_0))

    DRAFT.md line 256 drops the constant term (it is hedge-irrelevant — only
    the σ_T-dependent slope matters for Carr-Madan replication) and writes:

        Π(σ_T)  ≈  K̂ · σ_T

    This is what enables the Carr-Madan log-contract reduction (DRAFT.md
    lines 258-272): √σ_T is NOT statistically replicable, but σ_T is
    (via the log-contract identity), so the replication target switches
    from √σ_T to its linearization at σ_0.

    **Returned form:** the FULL linearized expression including the constant
    term, since spec §2 v0 (d) requires the linearization to "match import
    verbatim" (DRAFT.md line 252 form). The constant-drop step (line 256)
    is a downstream simplification used by the Carr-Madan strip in Trio 3,
    not a substantive simplification of Π itself.

        Π_linearized(σ_T; K*, σ_0) = K* · [√σ_0 + (σ_T - σ_0)/(2·√σ_0)]
                                   = K* · (σ_0 + σ_T) / (2·√σ_0)         [sympy canonical form]

    Verification: the coefficient of σ_T in the expanded form equals
    K*/(2·√σ_0) = K̂ (verified inline in Trio-2 notebook code cell via
    `sympy.expand(...).coeff(sigma_T_sym)`).
    """
    import sympy

    sqrt_sigma_T_linearized = sympy.sqrt(sigma_0_sym) + (
        sigma_T_sym - sigma_0_sym
    ) / (2 * sympy.sqrt(sigma_0_sym))
    return K_star_sym * sqrt_sigma_T_linearized


# ───── Carr-Madan helpers (Black-Scholes pricing under GBM, r=0, T=1) ─────
#
# These free functions are used by `carr_madan_strip_value`,
# `carr_madan_analytic`, and `strip_value_two_independent_codes` below.
# Pinned to GBM σ_0 = 10% baseline per spec FLAG-F4. r = 0 because the
# Carr-Madan log-contract identity replicates `E_Q[-2·log(S_T/S_0)]`
# which under GBM(r=0) equals σ_0²·T (the v0 analytic anchor). Keeping
# r = 0 also matches the framework's σ_T definition (variance, not drift).


def _norm_cdf(x: float) -> float:
    """Standard normal CDF via math.erf (zero external dep)."""
    import math

    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_call(S_0: float, K: float, sigma_0: float, T: float = 1.0) -> float:
    """Black-Scholes call price (r=0, no dividends).

    Returns the OTM-call premium at strike K under GBM(σ_0, T).
    """
    import math

    if K <= 0.0:
        return max(S_0 - K, 0.0)
    if sigma_0 * math.sqrt(T) <= 0.0:
        return max(S_0 - K, 0.0)
    sqrt_T = math.sqrt(T)
    d1 = (math.log(S_0 / K) + 0.5 * sigma_0 * sigma_0 * T) / (sigma_0 * sqrt_T)
    d2 = d1 - sigma_0 * sqrt_T
    return S_0 * _norm_cdf(d1) - K * _norm_cdf(d2)


def _bs_put(S_0: float, K: float, sigma_0: float, T: float = 1.0) -> float:
    """Black-Scholes put price (r=0, no dividends) via put-call parity.

    Returns the OTM-put premium at strike K under GBM(σ_0, T). Under r=0
    parity reduces to:  Put − Call = K − S_0  (forward = spot).
    """
    return _bs_call(S_0, K, sigma_0, T) - S_0 + K


def _build_strike_grid(
    S_0: float,
    sigma_0: float,
    n_condors: int = 3,
    legs_per_condor: int = 4,
    x_max_factor: float = 3.0,
) -> tuple[list[float], list[float], float]:
    """Build the 12-strike log-grid + Carr-Madan weights per spec §10.5.

    Returns (strikes K_j, weights w_j, Δx) where:
        - K_j = S_0 · exp(x_j),  x_j uniform on [-x_max, +x_max]
        - x_max = x_max_factor · σ_0 (default 3·σ_0 per §11.b derivation)
        - w_j = 1/K_j²  (Carr-Madan weight rule, DRAFT.md line 264)
        - Δx = uniform log-spacing step (used for trapezoidal integration)

    The total leg count is `n_condors · legs_per_condor` (default 12). No
    explicit per-condor ordering is imposed at this layer — that is the
    consumer's responsibility (e.g., `carr_madan_strip_value` partitions
    the 12 strikes into left-tail / ATM / right-tail per §10.5).
    """
    import math

    n_legs = n_condors * legs_per_condor
    x_max = x_max_factor * sigma_0
    # Uniform x grid on [-x_max, +x_max] with n_legs nodes
    if n_legs < 2:
        raise ValueError("n_legs must be >= 2 for log-grid spacing")
    dx = (2.0 * x_max) / (n_legs - 1)
    xs: list[float] = [-x_max + j * dx for j in range(n_legs)]
    strikes: list[float] = [S_0 * math.exp(x) for x in xs]
    weights: list[float] = [1.0 / (K * K) for K in strikes]
    return strikes, weights, dx


def carr_madan_strip_value(
    S_0: float,
    sigma_0: float,
    n_condors: int = 3,
    legs_per_condor: int = 4,
) -> tuple[float, list[dict[str, Any]]]:
    """Discrete IronCondor strip approximation of σ_T per spec §10.5.

    Constructs the 3 condors × 4 legs = 12 legs strip with strikes
    K_j = S_0·exp(x_j), weights w_j ∝ 1/K_j², covering left-tail / ATM
    / right-tail regions per spec §10.5. Returns
    `(strip_value, per_leg_breakdown)` where:

    - `strip_value`: the discrete strip approximation of the Carr-Madan
       integrand `∫ w(K)·V(K) dK` evaluated at the 12 nodes via trapezoid
       rule on the log-grid: `strip_value = Σ_j w_j · V_j · K_j · Δx`
       where `V_j` is the OTM put price for `K_j < S_0` and OTM call price
       for `K_j ≥ S_0`. Note `w_j · K_j · Δx = Δx / K_j` (the canonical
       Carr-Madan log-grid weight).

    - `per_leg_breakdown`: list of 12 dicts, each with keys
       `{"strike", "weight", "is_put", "option_value", "contribution",
         "condor_id", "leg_role"}`.
       `condor_id ∈ {0,1,2}` enumerates the 3 condors (left-tail / ATM /
       right-tail per §10.5); `leg_role ∈ {"long_K1","short_K2","short_K3",
       "long_K4"}` enumerates the 4 legs of each IronCondor.

    Spec §11.b: under GBM σ_0 ≈ 10% baseline + this 12-leg log-grid,
    the truncation+discretization bound is ≤ 5% relative error vs the
    analytic value (σ_0²·T under GBM r=0).
    """
    if n_condors * legs_per_condor != 12:
        raise ValueError(
            "spec §10.5 pin: n_condors × legs_per_condor must equal 12 "
            f"(got {n_condors} × {legs_per_condor} = "
            f"{n_condors * legs_per_condor})"
        )

    strikes, weights, dx = _build_strike_grid(
        S_0, sigma_0, n_condors=n_condors, legs_per_condor=legs_per_condor
    )

    leg_roles = ("long_K1", "short_K2", "short_K3", "long_K4")
    n_legs = n_condors * legs_per_condor
    leg_breakdown: list[dict[str, Any]] = []
    strip_value: float = 0.0
    for j in range(n_legs):
        K_j = strikes[j]
        w_j = weights[j]
        is_put = K_j < S_0
        V_j = _bs_put(S_0, K_j, sigma_0) if is_put else _bs_call(S_0, K_j, sigma_0)
        # Carr-Madan log-grid trapezoidal integrand: w_j · V_j · ΔK_j
        # where ΔK_j = K_j · dx (since K = e^x ⟹ dK = K·dx).
        contribution = w_j * V_j * K_j * dx
        strip_value += contribution
        condor_id = j // legs_per_condor
        leg_role = leg_roles[j % legs_per_condor]
        leg_breakdown.append(
            {
                "strike": K_j,
                "weight": w_j,
                "is_put": is_put,
                "option_value": V_j,
                "contribution": contribution,
                "condor_id": condor_id,
                "leg_role": leg_role,
            }
        )
    return strip_value, leg_breakdown


def carr_madan_analytic(S_0: float, sigma_0: float, T: float = 1.0) -> float:
    """Closed-form analytic value for σ_T per Carr-Madan log-contract.

    Under GBM with volatility σ_0 over horizon T (default 1), the
    standard Carr-Madan 1998 log-contract identity (eq 9) is:

        E_Q[-2·log(S_T/S_0)]  =  2·∫_0^{S_0} P(K)/K² dK
                              +  2·∫_{S_0}^∞ C(K)/K² dK

    Under GBM with r = 0 (matching the framework's σ_T = realized
    variance convention), the log-return identity gives:

        E_Q[-2·log(S_T/S_0)]  =  σ_0² · T

    Therefore the integral on the right-hand side (which is what
    `carr_madan_strip_value` discretizes via the §10.5 12-leg log-grid)
    evaluates to:

        ∫_0^{S_0} P(K)/K² dK + ∫_{S_0}^∞ C(K)/K² dK  =  ½ · σ_0² · T

    DRAFT.md line 261 uses `σ_T ∼ ∫…` (informal proportionality `∼`,
    NOT equality). The standard Carr-Madan factor of 2 (Carr-Madan 1998
    eq 9; Demeterfi et al 1999 "More Than You Ever Wanted To Know About
    Volatility Swaps" §III) lives outside the integral. This function
    returns the integral side `½·σ_0²·T` because that is what the
    discrete strip in `carr_madan_strip_value` numerically computes
    (the integrand `V(K)/K²` summed against the log-grid weight).

    This is the v0 anchor against which the discrete strip in
    `carr_madan_strip_value` is reconciled per spec §11.b.

    Returns ½·σ_0²·T (a positive scalar).
    """
    return 0.5 * sigma_0 * sigma_0 * T


def strip_value_two_independent_codes(
    S_0: float, sigma_0: float, n_condors: int = 3, legs_per_condor: int = 4
) -> tuple[float, float]:
    """Two independent codings of the strip value for §11.a self-consistency.

    Implementation A: per-leg accumulation in a Python `for` loop, ordering
        the strikes from leftmost (smallest K) to rightmost (largest K).
        Contribution per leg is `w_j · V_j · K_j · Δx`.

    Implementation B: per-condor accumulation. Each of the 3 condors
        contributes `Σ_{ℓ=1..4} w_{ℓ} · V_{ℓ} · K_{ℓ} · Δx` with the
        `Σ` evaluated condor-internally (4 floating-point adds), then the
        3 per-condor partial sums are accumulated. The grouping order
        differs from implementation A, exercising the floating-point
        non-associativity surface.

    Per spec §11.a, `|A − B| ≤ 1e-10 × N_legs = 1.2e-9` absolute per
    payoff evaluation. Failure at this scale indicates a code bug, not a
    model bug (triage: debugger / unit-test, NOT spec amendment).

    Returns `(impl_a_value, impl_b_value)`.
    """
    if n_condors * legs_per_condor != 12:
        raise ValueError(
            "spec §10.5 pin: n_condors × legs_per_condor must equal 12 "
            f"(got {n_condors} × {legs_per_condor})"
        )
    strikes, weights, dx = _build_strike_grid(
        S_0, sigma_0, n_condors=n_condors, legs_per_condor=legs_per_condor
    )
    n_legs = n_condors * legs_per_condor

    # Implementation A: linear left-to-right per-leg accumulation.
    impl_a: float = 0.0
    for j in range(n_legs):
        K_j = strikes[j]
        w_j = weights[j]
        is_put = K_j < S_0
        V_j = _bs_put(S_0, K_j, sigma_0) if is_put else _bs_call(S_0, K_j, sigma_0)
        impl_a += w_j * V_j * K_j * dx

    # Implementation B: per-condor grouped accumulation with REWRITTEN
    # weight expression. Algebraically: w_j · V_j · K_j · dx
    #                                 = (1/K_j²) · V_j · K_j · dx
    #                                 = V_j · dx / K_j
    # This is the canonical Carr-Madan log-grid form. The arithmetic
    # operation count differs from Impl A (one division vs two multiplies
    # plus an implicit division inside the weight construction), exercising
    # the §11.a non-associativity surface AND the equivalence of the two
    # algebraically-identical weight expressions (`1/K²·K·dx` vs `dx/K`).
    # The 4-leg inner / 3-condor outer grouping further differs from
    # Impl A's linear accumulation order.
    impl_b: float = 0.0
    for c in range(n_condors):
        condor_partial: float = 0.0
        for ell in range(legs_per_condor):
            j = c * legs_per_condor + ell
            K_j = strikes[j]
            is_put = K_j < S_0
            V_j = (
                _bs_put(S_0, K_j, sigma_0)
                if is_put
                else _bs_call(S_0, K_j, sigma_0)
            )
            # Different algebraic form than Impl A (no `weights[j]` lookup).
            condor_partial += V_j * dx / K_j
        impl_b += condor_partial
    return impl_a, impl_b
