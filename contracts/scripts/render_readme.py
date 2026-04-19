"""Jinja2-backed README auto-render for the FX-vol-on-CPI-surprise chain.

Task 30 of the ``docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md``
plan. This module exposes a pure function ``render_readme`` that takes

  * ``gate_verdict``   — the dict shape produced by
                         ``scripts.gate_aggregate.build_gate_verdict``
                         (NB3 §10 artifact, ``estimates/gate_verdict.json``).
  * ``point_params``   — the dict shape produced by
                         ``scripts.nb2_serialize`` (NB2 §10 artifact,
                         ``estimates/nb2_params_point.json``).
  * ``template_path``  — path to the Jinja2 template file
                         (``Colombia/_readme_template.md.j2``).

and returns the rendered markdown as a UTF-8 string. The function is
fully deterministic: no wall-clock access, no randomness, no environment
inspection — given identical inputs the output is byte-identical across
processes and across runs. This is the precondition that enables the
CI diff check in Task 32 (and the ``test_readme_byte_identical_to_committed``
assertion in this task's own test suite) to detect silent drift between
the committed JSON artifacts and the committed ``README.md``.

The CLI entry point below is what CI invokes:

    python scripts/render_readme.py \\
        notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json \\
        notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb2_params_point.json

The rendered markdown is written to stdout. Callers redirect to the
target file (or compare the captured stdout against the committed
``README.md`` byte-for-byte).

Design choices:

  * Template undefined-policy: ``jinja2.StrictUndefined`` so a missing
    key in the JSON surfaces as a template error at render time rather
    than silently becoming an empty string in the rendered output.
  * ``trim_blocks=True`` and ``lstrip_blocks=True`` so ``{% ... %}`` tag
    whitespace does not leak into the rendered markdown.
  * Numeric formatting: every floating-point value routed through the
    template is pre-formatted to a fixed ``f"{x:.6f}"`` string in this
    module so the template itself has no numeric-formatting logic — the
    template is a "dumb" layout file; all arithmetic lives here.
  * CI normalisation of the 90% z-critical constant: ``1.6448536269514722``
    matches ``scipy.stats.norm.ppf(0.95)`` at the full 64-bit precision
    used in NB3 §8's forest-plot assembly; reusing that literal keeps
    the CIs identical across modules.
  * No numpy / scipy import — the module is deliberately pure stdlib +
    jinja2 so the CI diff check can run on the minimal packaging layer
    (pre-commit hook, standalone docker image) without importing the
    heavy econometrics stack.

Implementation reference: plan Task 30 (lines 547-561) + the
pre-committed per-section spec on plan line 557.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Final, Mapping

import jinja2


# ── Formatting constants ─────────────────────────────────────────────────

# 90% two-sided normal critical — scipy.stats.norm.ppf(0.95) at 64-bit
# precision. Hard-coded so this module does not import scipy.
_Z_90: Final[float] = 1.6448536269514722

# Canonical number format: 6 decimal places, fixed-point. Matches the
# precision of the committed JSON artifacts (which store IEEE-754
# double-precision floats serialised via json.dump). Using a fixed
# format here prevents cross-platform drift (e.g. Python 3.13's repr
# heuristics changing between point releases).
_FLOAT_FMT: Final[str] = "{:.6f}"


# ── Private helpers ──────────────────────────────────────────────────────

def _fmt_float(x: float) -> str:
    """Canonical 6-decimal float formatting used throughout the template.

    Routing every numeric value through this helper keeps the template
    purely a layout file: it never sees a bare ``float`` and therefore
    can never introduce locale-dependent formatting (e.g. a non-US
    decimal separator from ``str(x)``).
    """
    return _FLOAT_FMT.format(float(x))


def _primary_row(point_params: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the primary Column-6 β̂_CPI + HAC SE + 90% CI + n.

    The ``ols_primary`` block is the anchor specification for the whole
    pipeline; its ``cpi_surprise_ar1`` coefficient is what the gate
    headline summarises.
    """
    ols = point_params["ols_primary"]
    beta = float(ols["beta"]["cpi_surprise_ar1"])
    se = float(ols["se"]["cpi_surprise_ar1"])
    return {
        "beta_fmt": _fmt_float(beta),
        "se_fmt": _fmt_float(se),
        "ci_lo_fmt": _fmt_float(beta - _Z_90 * se),
        "ci_hi_fmt": _fmt_float(beta + _Z_90 * se),
        "n": int(ols["n"]),
        "hac_lag": int(ols.get("hac_lag", 4)),
        "date_min": str(ols["date_min"]),
        "date_max": str(ols["date_max"]),
    }


def _garch_row(point_params: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the GARCH-X δ̂_CPI + QMLE SE + 90% CI.

    The loading lives under ``garch_x.theta['delta']``; the SE is the
    square root of the diagonal entry of ``garch_x.cov.matrix`` at the
    index matching ``'delta'`` in ``cov.param_names``.
    """
    gx = point_params["garch_x"]
    delta = float(gx["theta"]["delta"])
    cov = gx["cov"]
    names = cov["param_names"]
    matrix = cov["matrix"]
    idx = names.index("delta")
    se = float(matrix[idx][idx]) ** 0.5
    # n for GARCH-X is not separately stored; reuse the primary n since
    # both fits are on the identical weekly panel (§1 fingerprint gate).
    n = int(point_params["ols_primary"]["n"])
    return {
        "beta_fmt": _fmt_float(delta),
        "se_fmt": _fmt_float(se),
        "ci_lo_fmt": _fmt_float(delta - _Z_90 * se),
        "ci_hi_fmt": _fmt_float(delta + _Z_90 * se),
        "n": n,
    }


def _decomp_rows(
    point_params: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Extract the decomposition β̂_CPI and β̂_PPI rows."""
    dec = point_params["decomposition"]
    b_cpi = float(dec["beta"]["cpi_surprise_ar1"])
    s_cpi = float(dec["se"]["cpi_surprise_ar1"])
    b_ppi = float(dec["beta"]["ipp_std"])
    s_ppi = float(dec["se"]["ipp_std"])
    n = int(dec["n"])
    cpi_row = {
        "beta_fmt": _fmt_float(b_cpi),
        "se_fmt": _fmt_float(s_cpi),
        "ci_lo_fmt": _fmt_float(b_cpi - _Z_90 * s_cpi),
        "ci_hi_fmt": _fmt_float(b_cpi + _Z_90 * s_cpi),
        "n": n,
    }
    ppi_row = {
        "beta_fmt": _fmt_float(b_ppi),
        "se_fmt": _fmt_float(s_ppi),
        "ci_lo_fmt": _fmt_float(b_ppi - _Z_90 * s_ppi),
        "ci_hi_fmt": _fmt_float(b_ppi + _Z_90 * s_ppi),
        "n": n,
    }
    return cpi_row, ppi_row


def _build_environment(template_path: Path) -> jinja2.Environment:
    """Jinja2 environment with strict-undefined + deterministic whitespace.

    ``StrictUndefined`` raises if the template references a missing key
    — a silent empty-string fill would be a latent drift hazard, so we
    force the error up to render time.

    ``keep_trailing_newline=True`` preserves the final newline in the
    template file so editors that strip trailing newlines on save do not
    change the rendered output byte-count.
    """
    loader = jinja2.FileSystemLoader(str(template_path.parent))
    return jinja2.Environment(
        loader=loader,
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=False,
    )


# ── Public pure function ──────────────────────────────────────────────────

def render_readme(
    gate_verdict: Mapping[str, Any],
    point_params: Mapping[str, Any],
    template_path: Path,
) -> str:
    """Render the FX-vol-on-CPI-surprise README markdown.

    Pure function. No file I/O other than reading the template file
    (which is the ONLY side channel, and it is deterministic given the
    committed template). No wall-clock. No randomness. Identical inputs
    + identical template ⇒ byte-identical output.

    Args:
        gate_verdict: The gate-verdict dict from NB3 §10.
        point_params: The NB2 point-parameter dict.
        template_path: Path to the ``_readme_template.md.j2`` file.

    Returns:
        The rendered markdown as a UTF-8 string. The trailing newline
        from the template is preserved.

    Raises:
        jinja2.UndefinedError: A template variable references a key
            missing from ``gate_verdict`` or ``point_params``.
        FileNotFoundError: ``template_path`` does not exist.
    """
    template_path = Path(template_path)
    env = _build_environment(template_path)
    template = env.get_template(template_path.name)

    primary = _primary_row(point_params)
    garch = _garch_row(point_params)
    decomp_cpi, decomp_ppi = _decomp_rows(point_params)

    # The three PDF relative paths — matched to ``env.PDF_DIR`` as a
    # sibling of README.md (``Colombia/pdf/``). The template itself
    # just concatenates the relative prefix with the notebook stem so
    # the paths always track env.py's NB*_PATH constants.
    nb1_pdf = "pdf/01_data_eda.pdf"
    nb2_pdf = "pdf/02_estimation.pdf"
    nb3_pdf = "pdf/03_tests_and_sensitivity.pdf"

    rendered = template.render(
        gate_verdict=gate_verdict,
        point_params=point_params,
        primary=primary,
        garch=garch,
        decomp_cpi=decomp_cpi,
        decomp_ppi=decomp_ppi,
        nb1_pdf_relpath=nb1_pdf,
        nb2_pdf_relpath=nb2_pdf,
        nb3_pdf_relpath=nb3_pdf,
    )
    return rendered


# ── CLI entry point ──────────────────────────────────────────────────────

def _cli(argv: list[str]) -> int:
    """Console entry: ``render_readme.py <gate_json> <point_json>``.

    Writes the rendered markdown to stdout. The template path is
    resolved relative to the repository layout: the Colombia
    notebook directory sits alongside ``Colombia/`` three parents up
    from this script file. This keeps the CLI useful without demanding
    a third positional argument.
    """
    if len(argv) != 3:
        print(
            "Usage: render_readme.py <gate_verdict.json> "
            "<nb2_params_point.json>",
            file=sys.stderr,
        )
        return 2

    gate_path = Path(argv[1])
    point_path = Path(argv[2])

    if not gate_path.is_file():
        print(f"gate_verdict.json not found: {gate_path}", file=sys.stderr)
        return 1
    if not point_path.is_file():
        print(f"nb2_params_point.json not found: {point_path}", file=sys.stderr)
        return 1

    with open(gate_path, "r", encoding="utf-8") as fh:
        gate_verdict = json.load(fh)
    with open(point_path, "r", encoding="utf-8") as fh:
        point_params = json.load(fh)

    # Canonical template location: Colombia/_readme_template.md.j2. We
    # resolve it relative to this script's parents[1] (scripts/.. =
    # contracts/) plus the known subpath.
    contracts_dir = Path(__file__).resolve().parents[1]
    template_path = (
        contracts_dir
        / "notebooks"
        / "fx_vol_cpi_surprise"
        / "Colombia"
        / "_readme_template.md.j2"
    )

    rendered = render_readme(gate_verdict, point_params, template_path)
    sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":  # pragma: no cover — exercised by CLI test
    raise SystemExit(_cli(sys.argv))
