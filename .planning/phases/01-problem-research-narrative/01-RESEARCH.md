# Phase 1: Problem & Research Narrative - Research

**Researched:** 2026-03-18
**Domain:** Research synthesis, narrative writing, publication-style data visualization
**Confidence:** HIGH

## Summary

Phase 1 produces the narrative text that downstream phases (root README in Phase 3, research README in Phase 3, and Beamer slides in Phase 4) consume. The phase covers three requirements: PROB-01 (adverse competition problem statement), PROB-02 (quadratic deviation hazard model summary), and PROB-03 (key statistics presented accessibly). No diagrams, no slide formatting, no code changes -- pure narrative and publication-ready plots.

The research artifacts already exist in complete form: econometrics.tex contains the full model specification with all tables and equations, the notebooks contain working code that produces all required plots, and the backtest module has plotting functions. The primary work is (1) distilling these into presentation-ready markdown narratives, (2) upgrading matplotlib plots to publication style with `usetex`, and (3) exporting the 4 required PNGs to a `research/figures/` directory.

**Primary recommendation:** Write two markdown narrative files (`research/narrative/problem.md` and `research/narrative/research-summary.md`) as the single source of truth. Downstream phases copy/adapt from these. Update notebook plotting to use publication-style rcParams with LaTeX rendering. Export plots to `research/figures/`.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Opening hook: "There's a latent risk that discourages passive liquidity providers -- and no current hedging instrument tracks it on-chain"
- Frame as **adverse competition**, not healthy competition -- reference Capponi, Jia & Zhu (2024) on JIT substituting (not complementing) passive LPs, which decreases market quality
- Concrete example: walk through one passive LP's experience in ETH/USDC 30bps -- deposits, JIT enters, fee share drops from 1/N to x_k << 1/N, eventually exits
- Two key risk properties: (1) path-dependent tail risk (1 trigger day in 41), (2) completely orthogonal to IL/LVR
- All five papers cited explicitly: Capponi-Jia-Zhu, Capponi-Zhu, Ma-Crapis, Aquilina et al., Bichuch-Feinstein
- Full equation + coefficient table + econometric interpretation from main.pdf Section 5.7
- Three pillars: demand exists / price exists / backtest validates
- 4 backtest PNGs (publication style), 2 mermaid-to-PNG (Phase 2), 4 LaTeX-native elements (Phase 4)
- Re-run notebooks for plots, publication style with usetex
- Narrative flow: Problem -> Evidence -> Solution -> Demo -> Roadmap

### Claude's Discretion
- Exact wording of narrative transitions between sections
- How to simplify equations for mixed audience (whether to add plain-English annotations alongside LaTeX)
- PNG output resolution and figure sizing for Beamer

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PROB-01 | Presentation opens with adverse competition problem -- fee concentration is orthogonal to LVR, passive LPs face unhedged risk | econometrics.tex Sections 5.1-5.3 (theoretical foundations), all 5 papers, the concrete LP example walkthrough |
| PROB-02 | Research summary covers quadratic deviation hazard model, inverted-U finding, turning point delta* ~ 0.09 | econometrics.tex Sections 5.4-5.8 (model, estimation, results, interpretation), payoff.tex Sections 1-2 (FCI definition, quadratic hazard) |
| PROB-03 | Key statistics presented accessibly (41 days, 600 positions, 2.65x real vs null, 63% of days with positive deviation) | econometrics.tex Section 5.1 (empirical properties table), backtest notebook Section 1 (trigger days), notebook Sections 8-10 (p-squared payoff results) |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| matplotlib | 3.10.8 | Publication-style plots with LaTeX rendering | Already installed in uhi8 venv; `usetex` mode produces Beamer-compatible typography |
| pdflatex | TeX Live 2026/dev | LaTeX rendering for matplotlib usetex and Beamer compilation | Already installed system-wide |
| jupyter nbconvert | (in uhi8) | Headless notebook execution for plot generation | Already configured in Makefile `notebooks` target |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @mermaid-js/mermaid-cli | latest via npx | Export mermaid diagrams to PNG | Phase 2 only -- not needed in Phase 1 |
| numpy | (in uhi8) | Array operations for plot data | Already a dependency of backtest modules |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| matplotlib usetex | Plain matplotlib | usetex matches Beamer typography exactly; plain mode would create visual mismatch |
| Separate narrative files | Inline in README | Separate files allow reuse across README and Beamer without duplication |

**Installation:**
No new packages needed. All dependencies already exist in the `uhi8` venv and system.

**Version verification:** matplotlib 3.10.8 confirmed via `uhi8/bin/python -c "import matplotlib; print(matplotlib.__version__)"`. pdfTeX confirmed as TeX Live 2026/dev.

## Architecture Patterns

### Recommended Project Structure
```
research/
  narrative/                  # NEW: presentation-ready markdown narratives
    problem.md                # PROB-01: adverse competition problem statement
    research-summary.md       # PROB-02 + PROB-03: model, results, statistics
  figures/                    # NEW: publication-style PNGs for README and Beamer
    dose-response.png         # Q1-Q4 exit rates by deviation quartile
    trigger-days.png          # Daily delta-plus bar chart with trigger threshold
    alpha-sweep.png           # % better off and mean HV vs tail exponent
    reserve-dynamics.png      # Seeded reserve trajectories at gamma*
  backtest/
    plotting.py               # MODIFY: add publication rcParams setup function
  notebooks/
    eth-usdc-insurance-demand-identification.ipynb  # MODIFY: add figure export cells
    eth-usdc-backtest.ipynb                         # MODIFY: add figure export cells
  model/
    preamble.tex              # READ ONLY: extract macros for Beamer (Phase 4)
```

### Pattern 1: Narrative-as-Source-of-Truth
**What:** Write narrative content in standalone markdown files under `research/narrative/`. Downstream phases (README, Beamer) consume these files by reference or adapted copy.
**When to use:** Always for this project -- avoids maintaining the same narrative in three places.
**Rationale:** The CONTEXT.md specifies that Phase 1 produces "narrative text that downstream phases consume." Standalone files make this explicit and prevent drift.

### Pattern 2: Publication rcParams Module
**What:** A single function that sets all matplotlib rcParams for publication style. Called at the top of each notebook before any plotting.
**When to use:** Every notebook that produces figures for the presentation.
**Example:**
```python
# Source: matplotlib.org/stable/users/explain/text/usetex.html
def set_publication_style() -> None:
    """Configure matplotlib for Beamer-compatible publication plots."""
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "text.usetex": True,
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.figsize": (5.0, 3.5),    # Beamer 128mm x 96mm at 100dpi
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
    })
```

### Pattern 3: Three-Pillar Narrative Structure
**What:** The research summary is organized around three pillars as specified in CONTEXT.md:
1. **Demand exists** -- negative beta1 flipping to positive beta2 proves contingent demand when Delta > delta*
2. **A price exists** -- marginal effect translates to implied premium ($110/position at Delta=0.15)
3. **Backtest validates** -- p-squared payoff shows 18.8% of positions better off, positive mean hedge value

**When to use:** This is the locked organizing principle for the research summary narrative.

### Anti-Patterns to Avoid
- **Duplicating narrative text across files:** Write once in `research/narrative/`, reference elsewhere
- **Hardcoding statistics in prose:** Extract key numbers as a structured summary at the top of each narrative file so they can be updated from a single place if the underlying data ever changes
- **Mixing narrative and formatting:** Phase 1 produces pure text + PNGs. Beamer formatting is Phase 4's job.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LaTeX font rendering in plots | Custom font loading | `plt.rcParams["text.usetex"] = True` | Handles font metrics, kerning, math mode automatically |
| Figure sizing for Beamer | Manual pixel calculations | `figure.figsize = (5.0, 3.5)` with 300 DPI | Beamer default slide is 128mm x 96mm; 5x3.5 inches at 300dpi gives clean scaling |
| Mermaid to PNG | Screenshot or manual export | `npx @mermaid-js/mermaid-cli -i input.mmd -o output.png` | Consistent rendering, scriptable, reproducible (Phase 2) |
| Narrative structure | Free-form writing | Three-pillar template from CONTEXT.md | User locked this structure; following it prevents revision cycles |

**Key insight:** The research is already complete. Phase 1 is a distillation and visualization task, not a research task. Every statistic, equation, and coefficient already exists in the LaTeX source and notebooks.

## Common Pitfalls

### Pitfall 1: usetex Fails Silently or Errors
**What goes wrong:** `text.usetex: True` requires a working LaTeX installation with specific packages (geometry, inputenc, type1cm loaded automatically). Missing fonts or packages cause cryptic errors.
**Why it happens:** System LaTeX installations vary. The `dvipng` or `dvisvgm` backend may not be installed.
**How to avoid:** Test with a minimal script first: `python -c "import matplotlib.pyplot as plt; plt.rcParams['text.usetex']=True; fig,ax=plt.subplots(); ax.set_xlabel(r'$\Delta^+$'); fig.savefig('/tmp/test.png')"`. Verify dvipng is available: `which dvipng`.
**Warning signs:** `RuntimeError: Failed to process string with tex` or missing `dvipng` errors.

### Pitfall 2: Notebook State Pollution
**What goes wrong:** Notebooks executed headless via `make notebooks` may have stale cell outputs or import errors if `sys.path.insert` doesn't resolve correctly.
**Why it happens:** The Makefile sets `PYTHONPATH=research` but notebooks also do `sys.path.insert(0, "..")`. Working directory depends on how nbconvert is invoked.
**How to avoid:** The Makefile already uses `--ExecutePreprocessor.kernel_name=thetaswap` which has PYTHONPATH set correctly. Add figure-saving cells that use absolute paths: `fig.savefig(Path(__file__).parent.parent / "figures" / "name.png")` or use environment variable.
**Warning signs:** `ModuleNotFoundError` during headless execution.

### Pitfall 3: Narrative Too Dense for Mixed Audience
**What goes wrong:** The econometric content is highly technical. Copying equations directly from econometrics.tex makes the narrative inaccessible.
**Why it happens:** The source material is a mathematical specification, not a presentation.
**How to avoid:** Follow the CONTEXT.md guidance: "A reader with no DeFi background can explain in one sentence what adverse competition risk is and why it differs from impermanent loss." Lead with plain English, then support with equations. Add annotations to each equation.
**Warning signs:** The problem statement requires DeFi knowledge to understand the first paragraph.

### Pitfall 4: Figure Path Mismatch Between Notebook and Beamer
**What goes wrong:** Notebooks save PNGs to one path, but Beamer `\includegraphics` expects another.
**Why it happens:** Relative paths resolve differently in notebook working directory vs LaTeX compilation directory.
**How to avoid:** Save all PNGs to `research/figures/` with absolute paths from the notebook. Beamer (Phase 4) will use `\graphicspath{{../research/figures/}}` or similar.
**Warning signs:** Missing images in compiled PDF.

## Code Examples

### Publication-Style rcParams Setup
```python
# Source: matplotlib.org/stable/users/explain/text/usetex.html
# Source: matplotlib.org/stable/users/explain/customizing.html
import matplotlib.pyplot as plt

PUBLICATION_RCPARAMS = {
    # LaTeX rendering
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
    # Sizing for Beamer slides (128mm x 96mm content area)
    "figure.figsize": (5.0, 3.5),
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    # Font sizes matching Beamer 11pt base
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    # Clean style
    "axes.grid": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
}

plt.rcParams.update(PUBLICATION_RCPARAMS)
```

### Figure Export Pattern for Notebooks
```python
# At end of each plot cell, save to research/figures/
from pathlib import Path

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

fig.savefig(FIGURES_DIR / "dose-response.png")
plt.show()
```

### LaTeX Macros to Carry into Beamer (from preamble.tex)
```latex
% These macros from research/model/preamble.tex MUST be reused in Beamer preamble
% to ensure notation consistency. Phase 4 will \input a shared macro file.

% Fee concentration index (primary state)
\newcommand{\AT}{A_T}
\newcommand{\ThetaSum}{\Theta}
\newcommand{\PosCount}{N}
\newcommand{\ATnull}{A_T^{1/\PosCount}}
\newcommand{\DeltaPlus}{\Delta^{+}}
\newcommand{\DeltaStar}{\Delta^{*}}
\newcommand{\thetapos}{\theta}

% Insurance CFMM notation
\newcommand{\premfactor}{\gamma}
\newcommand{\pstar}{p^{*}}

% These are the minimum set needed for Phase 1 narrative equations.
% Full set is in research/model/preamble.tex.
```

### Narrative File Template
```markdown
<!-- research/narrative/problem.md -->
# The Adverse Competition Problem

> Opening hook per CONTEXT.md

## The Risk Nobody Hedges

[Plain English: what adverse competition is, concrete LP example]

## Why This Is Different from Impermanent Loss

[Two properties: path-dependent tail risk, orthogonal to IL/LVR]

## What the Literature Says

[5 papers, each with one-sentence contribution + our confirmation]

## Key Statistics

| Statistic | Value | Source |
|-----------|-------|--------|
| Observation window | 41 days (2025-12-05 to 2026-01-14) | Dune Q6 |
| Positions analyzed | 600 | Dune Q4v2 |
| Real/Null A_T ratio | 2.65x | econometrics.tex Table 5.1 |
| Days with Delta > 0 | 63% (26/41) | econometrics.tex Table 5.1 |
| Trigger days (Delta > delta*) | 1 in 41 | backtest notebook Section 1 |
```

## Content Distillation Guide

This section provides the actual content the planner needs to structure tasks around. All content below is extracted from the canonical LaTeX sources and notebooks.

### Problem Statement Content (PROB-01)

**Opening hook:** "There's a latent risk that discourages passive liquidity providers -- and no current hedging instrument tracks it on-chain."

**Core argument chain:**
1. Passive LPs in Uniswap V3/V4 pools face fee dilution from sophisticated/JIT LPs (Capponi, Jia & Zhu 2024: JIT substitutes, does not complement, passive LP activity)
2. This is adverse competition: 7% of LP addresses capture 80% of fees (Aquilina et al. 2024, BIS)
3. A passive LP deposits in ETH/USDC 30bps. JIT enters. Fee share drops from 1/N to x_k << 1/N. Effective fee rate drops. Per Capponi & Zhu (2024), lower effective fee rate means lower exit threshold -- LP exits earlier.
4. Two properties make this hedgeable: (a) path-dependent tail risk (rare but severe: 1 trigger day in 41), (b) completely orthogonal to IL/LVR (IL coefficient does not absorb the concentration effect)
5. No existing product hedges this risk. Options hedge price risk. LVR products hedge MEV. Nothing hedges fee concentration.

**Literature one-liners:**
- **Capponi, Jia & Zhu (2024):** JIT liquidity crowds out passive LPs by substituting their fee share, not complementing it
- **Capponi & Zhu (2024):** LPs have optimal exit thresholds; lower effective fee rate means earlier exit
- **Ma & Crapis (2024):** Equal fee share (1/N) is the competitive equilibrium baseline -- deviation from this is the treatment variable
- **Aquilina et al. (2024, BIS):** 7% of LP addresses capture 80% of fees empirically
- **Bichuch & Feinstein (2024):** LP fee rate is priceable as a derivative; fixed-for-floating fee swap is structurally identical to ThetaSwap

### Research Summary Content (PROB-02 + PROB-03)

**Pillar 1 -- Demand Exists:**
- Quadratic deviation exit hazard model (econometrics.tex eq. 5.6): P(exit) = sigma(beta0 + beta1*Delta + beta2*Delta^2 + beta3*IL + beta4*log(age))
- Key result: beta1 = -23.18 (p=0.012), beta2 = +129.20 (p=0.030) at lag 1
- Inverted-U: below delta* ~ 0.09, concentration is protective (shelter regime); above it, drives exits (Capponi regime)
- Turning point formula: delta* = -beta1/(2*beta2) ~ 0.090
- Signal strong at lags 1-3, dissipates at 5-7 (short-memory PLP reaction)

**Pillar 2 -- A Price Exists:**
- Marginal effect: dP/dDelta = (beta1 + 2*beta2*Delta) * P_bar * (1 - P_bar)
- At Delta = 0.15: marginal effect = 2.27, meaning +0.01 in Delta raises exit probability by ~2.3 percentage points
- Insurance pricing: 2.3pp * 48 hours remaining * $100/hr = $110 implied premium per position
- This is the maximum willingness-to-pay for protection against concentration above the turning point

**Pillar 3 -- Backtest Validates:**
- p-squared exit payoff: payout = premium * ((max_p / p*)^2 - 1)^+
- At R0 = $200K seed capital, gamma = 3.30%: 18.8% of positions better off hedged, mean HV = +$23.21
- Comparison vs trigger-based (INS-05): 4.7% better off vs 18.8%; mean HV -$82.65 vs +$23.21
- No moral hazard: staying in pool during spikes increases payout
- Positive correlation between position lifetime and hedge value (correct incentive alignment)

**Key statistics (PROB-03):**

| Statistic | Value | Source |
|-----------|-------|--------|
| Observation window | 41 days | econometrics.tex Section 5.9 |
| Positions | 600 | econometrics.tex Section 5.9 |
| Position-day observations | 3,365 | econometrics.tex Section 5.7 |
| Exit events | 597 | econometrics.tex Section 5.7 |
| Real/Null A_T ratio | 2.65x | econometrics.tex Section 5.1 |
| Days with Delta > 0 | 63% (26/41) | econometrics.tex Section 5.1 |
| Trigger days (Delta > 0.09) | 1 in 41 | backtest notebook |
| Turning point delta* | ~0.09 | econometrics.tex Section 5.7 |
| beta1 (shelter) | -23.18, p=0.012 | econometrics.tex Section 5.7 |
| beta2 (Capponi) | +129.20, p=0.030 | econometrics.tex Section 5.7 |
| Implied premium at Delta=0.15 | $110/position | econometrics.tex Section 5.8.3 |
| p^2 payoff: % better off | 18.8% | backtest notebook Section 10 |
| p^2 payoff: mean HV | +$23.21 | backtest notebook Section 10 |
| Calibrated gamma | 3.30% | backtest notebook Section 2 |

### Four Required PNGs

1. **dose-response.png** -- Bar chart of exit rates by Delta quartile (Q1-Q4). Source: demand-identification notebook, cell "dose-response". Shows inverted-U pattern: Q1-Q2 baseline ~17.8%, Q3 peak 20.6%, Q4 drops 14.4%.

2. **trigger-days.png** -- Daily Delta+ bar chart with horizontal line at delta* = 0.09. Source: backtest notebook, cell "2f4p9s42dpk". Shows 1 trigger day (Dec 23, Delta+ = 0.158) out of 41.

3. **alpha-sweep.png** -- Three-panel figure: % better off vs alpha, mean HV vs alpha, HV distribution for alpha=2. Source: backtest notebook, cell "ghmgcuc3bfa". Shows alpha=2 as sweet spot.

4. **reserve-dynamics.png** -- Reserve trajectories: unseeded vs seeded (R0 = 50K, 100K, 200K, 500K). Source: backtest notebook, cell "ss66hox38i". Shows how seed capital resolves bootstrapping.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Trigger-based payout (INS-05) | p-squared exit payoff (alpha=2) | Backtest results (this research) | 0% -> 18.8% positions better off; eliminates bootstrapping problem |
| Linear A_T model | Quadratic deviation model | Spec progression (5 failed linear specs) | Reveals inverted-U; linear misses the shelter regime |
| A_T in levels as treatment | Deviation from 1/N null | Ma-Crapis null insight | Removes confounding from pool health/volume |

## Open Questions

1. **Plain-English annotations alongside equations**
   - What we know: CONTEXT.md says Claude's discretion on "how to simplify equations for mixed audience"
   - What's unclear: How much annotation is enough without being patronizing
   - Recommendation: Add a plain-English sentence before each equation and a "translation" sentence after. For the hazard model: "The exit probability depends on concentration deviation (Delta), its square (capturing the inverted-U), impermanent loss (IL), and how long the position has been alive (age)."

2. **Figure sizing for Beamer vs README**
   - What we know: Beamer content area is ~128mm x 96mm. README renders at arbitrary widths.
   - What's unclear: Whether to produce two sizes or one
   - Recommendation: Produce at 300 DPI, 5x3.5 inches (suitable for Beamer). README will scale automatically. One size fits both.

3. **Narrative file format for downstream consumption**
   - What we know: Phase 3 (READMEs) and Phase 4 (Beamer) need the same content in different formats
   - What's unclear: Whether markdown with inline LaTeX math (GitHub renders it) is sufficient, or if we need separate LaTeX snippets
   - Recommendation: Use markdown with `$...$` math notation (GitHub supports it). Phase 4 will extract and convert to Beamer `\begin{frame}` blocks. The narrative files are the single source; conversion is the downstream phase's job.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (in uhi8 venv) |
| Config file | research/tests/ (existing structure) |
| Quick run command | `cd research && ../uhi8/bin/python -m pytest tests/ -v -x` |
| Full suite command | `cd research && ../uhi8/bin/python -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROB-01 | Problem narrative file exists and contains required sections | smoke | `test -f research/narrative/problem.md && grep -q "adverse competition" research/narrative/problem.md` | No -- Wave 0 |
| PROB-02 | Research summary contains model equation, coefficient table, turning point | smoke | `test -f research/narrative/research-summary.md && grep -q "inverted-U" research/narrative/research-summary.md` | No -- Wave 0 |
| PROB-03 | Key statistics appear in research summary | smoke | `grep -c "41 days\|600 positions\|2.65" research/narrative/research-summary.md` | No -- Wave 0 |
| PROB-01/02/03 | Publication PNGs exist and are non-empty | smoke | `test -s research/figures/dose-response.png && test -s research/figures/trigger-days.png && test -s research/figures/alpha-sweep.png && test -s research/figures/reserve-dynamics.png` | No -- Wave 0 |
| N/A | Existing backtest tests still pass after plotting.py changes | regression | `cd research && ../uhi8/bin/python -m pytest tests/backtest/ -v -x` | Yes |
| N/A | Notebooks execute headless without errors | integration | `make notebooks` | Yes (Makefile) |

### Sampling Rate
- **Per task commit:** `cd research && ../uhi8/bin/python -m pytest tests/backtest/ -v -x` (existing tests)
- **Per wave merge:** `make notebooks` (full headless notebook execution)
- **Phase gate:** All 4 PNGs exist in research/figures/, both narrative files exist, `make notebooks` passes

### Wave 0 Gaps
- [ ] `research/narrative/` directory -- does not exist yet, needs creation
- [ ] `research/figures/` directory -- does not exist yet, needs creation
- [ ] Publication rcParams function in `research/backtest/plotting.py` -- needs to be added
- [ ] Figure-saving cells in notebooks -- need to be added to existing notebooks

## Sources

### Primary (HIGH confidence)
- `research/model/econometrics.tex` -- Full econometric specification, all coefficients, tables, and interpretations. Read in full.
- `research/model/payoff.tex` -- FCI definition, co-primary state, DeltaPlus, price mapping. Read in full.
- `research/model/main.tex` -- Abstract summarizing the full story. Read in full.
- `research/model/preamble.tex` -- All LaTeX macros (AT, ATnull, DeltaPlus, DeltaStar, etc.). Read in full.
- `research/notebooks/eth-usdc-insurance-demand-identification.ipynb` -- Dose-response plots, lag sensitivity. Read in full.
- `research/notebooks/eth-usdc-backtest.ipynb` -- Trigger days, reserve dynamics, alpha sweep, p-squared payoff. Read in full.
- `research/backtest/plotting.py` -- Existing plot functions (money_plot, reserve_plot, hedge_distribution_plot). Read in full.

### Secondary (MEDIUM confidence)
- [matplotlib usetex docs](https://matplotlib.org/stable/users/explain/text/usetex.html) -- LaTeX text rendering configuration
- [matplotlib rcParams docs](https://matplotlib.org/stable/users/explain/customizing.html) -- Style customization
- [mermaid-cli GitHub](https://github.com/mermaid-js/mermaid-cli) -- CLI tool for mermaid diagram export (Phase 2)
- [Beamer user guide](https://tug.ctan.org/macros/latex/contrib/beamer/doc/beameruserguide.pdf) -- Shared preamble patterns

### Tertiary (LOW confidence)
None -- all findings verified against primary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools already installed and verified (matplotlib 3.10.8, pdfTeX, uhi8 venv)
- Architecture: HIGH -- narrative-as-source-of-truth pattern is straightforward; file structure follows existing conventions
- Content distillation: HIGH -- all statistics and equations extracted directly from LaTeX sources and notebook outputs
- Pitfalls: HIGH -- usetex requirements verified against system (pdflatex present); notebook execution tested via existing Makefile target

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable -- no external dependencies changing)
