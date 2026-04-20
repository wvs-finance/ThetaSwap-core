"""Tests for the Colombia nbconvert LaTeX template + companion config.

Task 6 of the econ-notebook-implementation plan. The notebook design spec
requires two PDF-export behaviors that the default ``jupyter nbconvert --to
latex`` pipeline does not give us out of the box:

  1. Cells tagged ``remove-input`` must render with their SOURCE suppressed
     but their OUTPUT preserved. These are the utility cells (imports, data
     loads, plot helpers) described in plan Rule 5 (Code visibility): the
     PDF reader sees the produced figure/table without a wall of boilerplate
     Python code first.
  2. The nbconvert execution timeout must be pinned to
     ``env.NBCONVERT_TIMEOUT`` (1800 s). Cold-start PDF exports of NB2/NB3
     run GARCH-X MLE + bootstrap + Bai-Perron changepoint search, which
     exceeds the nbconvert 600 s default.

Implementation shape (documented here so the test's expectations are clear):

  * ``article.tex.j2`` is a one-line Jinja2 file that extends nbconvert's
    bundled ``latex/index.tex.j2`` template. All hiding of tagged cells is
    delegated to ``TagRemovePreprocessor`` (wired in the config below), not
    to a template-level Jinja override. Rationale: the preprocessor is the
    officially documented path (see
    https://nbconvert.readthedocs.io/en/latest/removing_cells.html), is
    smaller to maintain, and stays robust across future template-layout
    changes in upstream jupyter-nbconvert.
  * ``jupyter_nbconvert_config.py`` enables ``TagRemovePreprocessor`` with
    ``remove_input_tags = {'remove-input'}`` and pins
    ``ExecutePreprocessor.timeout = env.NBCONVERT_TIMEOUT``. It reaches
    ``env.py`` via ``importlib.util.spec_from_file_location`` — the same
    pattern every other test in this suite uses — so the 1800 s literal
    lives in exactly one place (env.py) and any future bump auto-propagates.

Verification strategy:

  * In-process via ``nbconvert.exporters.LatexExporter`` (no subprocess).
    The subprocess path would require ``jupyter`` on PATH in CI and add
    ~1 s of launch cost per test with zero extra coverage.
  * A synthetic ``.ipynb`` is built in memory with ``nbformat`` — one
    markdown cell, one code cell tagged ``remove-input`` with a fabricated
    stream output, and one un-tagged code cell with a fabricated output.
    We assert four properties on the exported LaTeX:
      a) The markdown cell text survives (cell source untagged → visible).
      b) The tagged code cell's SOURCE (``x = 2 + 2``) is absent.
      c) The tagged code cell's OUTPUT sentinel is still present.
      d) The un-tagged code cell's source (``y = "visible"``) is present.
  * Separately, the config file is loaded as a ``TraitletsConfig`` and we
    assert ``c.ExecutePreprocessor.timeout == env.NBCONVERT_TIMEOUT``, plus
    ``c.TagRemovePreprocessor.remove_input_tags == {"remove-input"}`` and
    that the preprocessor is enabled.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Final

import nbformat
import pytest
from nbformat.v4 import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_output,
)

# ── Load env.py by file path (mirrors test_notebook_skeletons.py) ─────────

# This test file lives at: contracts/scripts/tests/test_nbconvert_template.py
# env.py lives at:         contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py
# contracts/ is parents[2] from here.
_ENV_PATH: Final[Path] = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
)


def _load_env():
    """Load env.py as a module by file path (it is not on sys.path)."""
    spec = importlib.util.spec_from_file_location("fx_vol_env", _ENV_PATH)
    assert spec is not None and spec.loader is not None, (
        f"Cannot build spec for {_ENV_PATH}"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_env = _load_env()

# ── Template + config paths ───────────────────────────────────────────────

_TEMPLATE_DIR: Final[Path] = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "_nbconvert_template"
)
TEMPLATE_FILE: Final[Path] = _TEMPLATE_DIR / "article.tex.j2"
CONFIG_FILE: Final[Path] = _TEMPLATE_DIR / "jupyter_nbconvert_config.py"

# Sentinels baked into the synthetic notebook.
#
# Design notes for the sentinels:
#
#   * LaTeX output escapes ``_`` to ``\_``, so sentinel strings that contain
#     underscores get fragmented in the rendered ``.tex``. To keep
#     substring assertions simple, the sentinels below use alphanumerics
#     only — no underscores, no special characters — so the literal string
#     appears in the output verbatim.
#   * Pygments tokenizes code-cell sources into per-token macros
#     (``\PY{n}{y} \PY{o}{=} ...``). Assertions for cell SOURCE must
#     therefore check for individual tokens (e.g. the identifier name)
#     rather than the full pre-export string. For the VISIBLE cell we
#     pick an identifier that survives Pygments tokenization as a single
#     contiguous token.
#
# ``HIDDEN_SOURCE_TOKEN`` is the identifier used in the tagged cell. After
# TagRemovePreprocessor strips the input, this token MUST NOT appear
# anywhere in the export. ``VISIBLE_SOURCE_TOKEN`` is the identifier in the
# un-tagged cell; it MUST appear in the export (inside a Pygments ``\PY``
# macro).
HIDDEN_SOURCE_TOKEN: Final[str] = "xhidden"  # full source: ``xhidden = 2 + 2``
HIDDEN_SOURCE_SENTINEL_SOURCE: Final[str] = f"{HIDDEN_SOURCE_TOKEN} = 2 + 2"
HIDDEN_OUTPUT_SENTINEL: Final[str] = "HIDDENoutputSENTINEL"

VISIBLE_SOURCE_TOKEN: Final[str] = "yvisible"  # full source: ``yvisible = 1``
VISIBLE_SOURCE_SENTINEL_SOURCE: Final[str] = f"{VISIBLE_SOURCE_TOKEN} = 1"
VISIBLE_OUTPUT_SENTINEL: Final[str] = "VISIBLEoutputSENTINEL"

MARKDOWN_SENTINEL: Final[str] = "MARKDOWNvisibleSENTINEL"


# ── Fixtures ──────────────────────────────────────────────────────────────

def _build_synthetic_notebook() -> nbformat.NotebookNode:
    """Build a minimal 3-cell notebook covering all four assertion paths.

    * Cell 0 (markdown): title + body containing ``MARKDOWN_SENTINEL``.
    * Cell 1 (code, tagged ``remove-input``): source ``x = 2 + 2`` with a
      pre-fabricated stream output containing ``HIDDEN_SOURCE_SENTINEL_OUTPUT``.
    * Cell 2 (code, no tag): source ``y = "visible"`` with a stream output
      containing ``VISIBLE_OUTPUT_SENTINEL``.

    Outputs are fabricated via ``nbformat.v4.new_output`` — no kernel
    execution needed, so the test is hermetic and fast.
    """
    md = new_markdown_cell(f"# Title\n\n{MARKDOWN_SENTINEL}")

    hidden = new_code_cell(source=HIDDEN_SOURCE_SENTINEL_SOURCE)
    hidden.outputs = [
        new_output(output_type="stream", name="stdout", text=HIDDEN_OUTPUT_SENTINEL)
    ]
    hidden.metadata["tags"] = ["remove-input"]
    # nbformat requires execution_count for code cells in v4 schema validation.
    hidden.execution_count = 1

    visible = new_code_cell(source=VISIBLE_SOURCE_SENTINEL_SOURCE)
    visible.outputs = [
        new_output(output_type="stream", name="stdout", text=VISIBLE_OUTPUT_SENTINEL)
    ]
    visible.execution_count = 2

    nb = new_notebook(cells=[md, hidden, visible])
    nbformat.validate(nb)
    return nb


def _load_config_as_traitlets():
    """Exec ``jupyter_nbconvert_config.py`` and return its ``c`` Config object.

    The config file is a plain Python script that expects ``get_config`` in
    its globals (the standard jupyter config protocol). We provide it and
    read ``c`` back out.
    """
    from traitlets.config import Config

    assert CONFIG_FILE.is_file(), f"Config file missing: {CONFIG_FILE}"
    c = Config()

    def get_config() -> Config:
        return c

    globals_dict: dict = {"get_config": get_config, "__file__": str(CONFIG_FILE)}
    code = compile(CONFIG_FILE.read_text(encoding="utf-8"), str(CONFIG_FILE), "exec")
    exec(code, globals_dict)  # noqa: S102 — trusted in-repo config
    return c


# ── Template-existence sanity ─────────────────────────────────────────────

def test_template_file_exists() -> None:
    """The custom LaTeX template file exists on disk."""
    assert TEMPLATE_FILE.is_file(), (
        f"Expected nbconvert LaTeX template at {TEMPLATE_FILE}"
    )


def test_config_file_exists() -> None:
    """The companion jupyter nbconvert config file exists on disk."""
    assert CONFIG_FILE.is_file(), (
        f"Expected jupyter_nbconvert_config.py at {CONFIG_FILE}"
    )


# ── LaTeX export assertions (preprocessor + template behavior) ────────────

def _export_synthetic_latex() -> str:
    """Export the synthetic notebook to LaTeX using our template + config.

    Returns the exported .tex body. Pure in-process — no subprocess.

    Note on exporter init: we load the jupyter config file first, then
    ATTACH the template-file path onto that same ``Config`` object under
    the ``LatexExporter`` namespace BEFORE constructing the exporter.
    Setting ``exporter.template_file`` after construction does not rewire
    the jinja ``template_paths`` list in this nbconvert version — the
    only reliable path is to pass the template via ``Config`` at init.
    """
    from nbconvert.exporters import LatexExporter

    nb = _build_synthetic_notebook()
    cfg = _load_config_as_traitlets()

    # Attach the template-file path to the same Config. LatexExporter's
    # ``_template_file_changed`` observer will split the absolute path into
    # (directory, filename) and push the directory onto extra_template_paths
    # before the jinja environment is built. See nbconvert/exporters/
    # templateexporter.py line ~236.
    cfg.LatexExporter.template_file = str(TEMPLATE_FILE)

    exporter = LatexExporter(config=cfg)
    body, _resources = exporter.from_notebook_node(nb)
    return body


def test_markdown_cell_text_is_preserved_in_latex() -> None:
    """Markdown cell content survives the export (untagged cells stay visible)."""
    body = _export_synthetic_latex()
    assert MARKDOWN_SENTINEL in body, (
        f"Expected markdown sentinel {MARKDOWN_SENTINEL!r} in LaTeX output. "
        f"First 500 chars:\n{body[:500]}"
    )


def test_tagged_cell_source_is_removed_from_latex() -> None:
    """Cell tagged ``remove-input`` has its source stripped from the export.

    We check that the identifier ``HIDDEN_SOURCE_TOKEN`` — chosen to be a
    unique alphanumeric string that does not appear anywhere else in the
    notebook or the default nbconvert template — is absent from the
    rendered LaTeX. If it were present, it would mean the
    TagRemovePreprocessor did not strip the input, and the full source
    would have been Pygment-tokenized into ``\\PY{n}{xhidden}`` etc.
    """
    body = _export_synthetic_latex()
    assert HIDDEN_SOURCE_TOKEN not in body, (
        f"Expected tagged-cell identifier {HIDDEN_SOURCE_TOKEN!r} "
        f"(from source {HIDDEN_SOURCE_SENTINEL_SOURCE!r}) to be ABSENT "
        f"from LaTeX output, but it was found. This means the "
        f"TagRemovePreprocessor did not strip the input. Body excerpt:\n"
        f"{body[:2000]}"
    )


def test_tagged_cell_output_is_preserved_in_latex() -> None:
    """Cell tagged ``remove-input`` keeps its output visible in the export."""
    body = _export_synthetic_latex()
    assert HIDDEN_OUTPUT_SENTINEL in body, (
        f"Expected tagged-cell output sentinel {HIDDEN_OUTPUT_SENTINEL!r} "
        f"to remain in LaTeX output (only the SOURCE should be hidden). "
        f"First 2000 chars:\n{body[:2000]}"
    )


def test_untagged_cell_source_is_preserved_in_latex() -> None:
    """Un-tagged code cell keeps its source visible (default behavior).

    Pygments tokenizes code cells into per-token ``\\PY{...}{...}`` macros,
    so the full pre-export source does not appear verbatim. We assert on
    the identifier token, which survives tokenization as a contiguous
    substring inside a single ``\\PY{n}{...}`` macro.
    """
    body = _export_synthetic_latex()
    assert VISIBLE_SOURCE_TOKEN in body, (
        f"Expected un-tagged code identifier {VISIBLE_SOURCE_TOKEN!r} "
        f"(from source {VISIBLE_SOURCE_SENTINEL_SOURCE!r}) to be PRESENT "
        f"in LaTeX output. First 2000 chars:\n{body[:2000]}"
    )


# ── Config-trait assertions (timeout pin + preprocessor wiring) ───────────

def test_config_pins_execute_timeout_to_env_value() -> None:
    """Config sets ExecutePreprocessor.timeout = env.NBCONVERT_TIMEOUT (1800)."""
    cfg = _load_config_as_traitlets()
    assert "ExecutePreprocessor" in cfg, (
        "Config must define ExecutePreprocessor.timeout to pin PDF-export "
        "runtime budget. Missing entirely."
    )
    actual = cfg.ExecutePreprocessor.timeout
    assert actual == _env.NBCONVERT_TIMEOUT, (
        f"ExecutePreprocessor.timeout must equal env.NBCONVERT_TIMEOUT "
        f"(={_env.NBCONVERT_TIMEOUT}). Got {actual!r}."
    )
    # Defence-in-depth: also pin the literal to 1800 so a rogue env.py edit
    # that drops the timeout doesn't silently pass.
    assert actual == 1800, (
        f"env.NBCONVERT_TIMEOUT drifted away from 1800 s. Got {actual!r}. "
        f"If this is intentional, update this assertion AND the notebook "
        f"design spec together."
    )


def test_config_enables_tagremove_preprocessor_for_remove_input_tag() -> None:
    """Config enables TagRemovePreprocessor with the ``remove-input`` tag."""
    cfg = _load_config_as_traitlets()
    assert "TagRemovePreprocessor" in cfg, (
        "Config must define TagRemovePreprocessor to strip utility-cell "
        "input from the PDF. Missing entirely."
    )
    tags = cfg.TagRemovePreprocessor.remove_input_tags
    # Accept either a set or a list in the config file — normalize to compare.
    assert set(tags) == {"remove-input"}, (
        f"TagRemovePreprocessor.remove_input_tags must be "
        f"exactly {{'remove-input'}}. Got {tags!r}."
    )
    assert cfg.TagRemovePreprocessor.enabled is True, (
        "TagRemovePreprocessor.enabled must be True, otherwise the "
        f"remove_input_tags setting is a no-op. Got "
        f"{cfg.TagRemovePreprocessor.enabled!r}."
    )


# ── Regression: missing env.py must RAISE, not silently fall back ─────────

def test_load_env_timeout_raises_when_env_missing(tmp_path: Path) -> None:
    """Loading the config with env.py absent must raise RuntimeError.

    Regression guard: the earlier revision of ``_load_env_timeout()`` emitted
    a ``RuntimeWarning`` and returned the literal ``1800`` when env.py could
    not be loaded. Because ``RuntimeWarning`` is not fatal by default, CI
    passed silently even when env.py structurally moved — the notebook suite
    then ran under a stale duplicated constant. The fix promotes the
    fallback to a hard ``RuntimeError``. This test locks that behavior.

    Strategy: copy the real config file into a throwaway temp directory
    WITHOUT an accompanying env.py. The config computes
    ``_ENV_PATH = Path(__file__).resolve().parent.parent / "env.py"`` at
    load time, so executing the copy with its ``__file__`` pointed at the
    temp location makes ``_ENV_PATH`` resolve to a non-existent file and
    triggers the ``is_file()`` guard. No patching, no monkey-business on
    ``Path.exists`` — just a clean, isolated filesystem layout that
    exercises the real code path end-to-end.

    The error message must name ``env.py`` (what went wrong),
    ``NBCONVERT_TIMEOUT`` (why it matters), and reference either
    ``parents[1]`` or ``just pre-commit-install`` (how to fix). We assert
    the two load-bearing substrings — the fix hints — are present.
    """
    from traitlets.config import Config

    # Lay out the temp dir to mirror the real on-disk structure:
    #   tmp_path/_nbconvert_template/jupyter_nbconvert_config.py  ← copy
    #   tmp_path/env.py                                           ← ABSENT
    fake_template_dir = tmp_path / "_nbconvert_template"
    fake_template_dir.mkdir()
    fake_config = fake_template_dir / "jupyter_nbconvert_config.py"
    fake_config.write_text(CONFIG_FILE.read_text(encoding="utf-8"), encoding="utf-8")

    # Sanity: ensure env.py is genuinely absent in the fake layout so the
    # test is actually exercising the failure path and not passing by
    # accident.
    assert not (tmp_path / "env.py").exists(), (
        f"Test setup invariant violated: {tmp_path / 'env.py'} must NOT "
        f"exist for this regression test to exercise the failure path."
    )

    c = Config()

    def get_config() -> Config:
        return c

    globals_dict: dict = {"get_config": get_config, "__file__": str(fake_config)}
    code = compile(fake_config.read_text(encoding="utf-8"), str(fake_config), "exec")

    # ``match`` uses a regex — escape the literal substrings we care about.
    # We match on ``env.py`` AND ``NBCONVERT_TIMEOUT`` to lock both halves
    # of the 3-part error message (what went wrong + why it matters).
    with pytest.raises(RuntimeError, match=r"env\.py.*NBCONVERT_TIMEOUT"):
        exec(code, globals_dict)  # noqa: S102 — trusted in-repo config
