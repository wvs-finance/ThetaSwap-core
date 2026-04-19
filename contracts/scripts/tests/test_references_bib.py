"""Tests for references.bib — the single source of truth for notebook citations.

Task 2 of the econ-notebook-implementation plan. The three notebooks
(01_data_eda, 02_estimation, 03_tests_and_sensitivity) emit citation blocks
and nbconvert LaTeX PDFs that resolve every citation through this file.

Assertions (per plan Rev 2, updated 2026-04-18 Task 15 citation integrity fix
and Model QA MEDIUM follow-up for Decision #11 KPSS attribution):
  * The file exists at contracts/notebooks/fx_vol_cpi_surprise/Colombia/references.bib
  * All 38 required BibTeX keys are present (35 original + 2 Colombian-canon
    anchors for Decision #6 added 2026-04-18 after Reality Checker review:
    anzoateguiGalvis2019comunicacion, galvisOliveiraAnzoategui2017anuncios;
    + 1 KPSS-under-heteroskedasticity technical anchor added 2026-04-18 after
    Model QA MEDIUM finding on Decision #11 attribution:
    cavaliereTaylor2005wildKPSS).
  * Every entry has a non-empty journal OR booktitle field (whichever is
    appropriate for its entry type).
  * Han-Kristensen 2014 is explicitly in the Journal of Business & Economic
    Statistics (NOT Journal of Econometrics — this correction was applied
    in plan revision 2).
  * Every entry carries either a `doi` or a `url` field (populated) so the
    reference is verifiable.

The tests use bibtexparser 1.4.x: parse with bibtexparser.load(open(path)),
iterate over database.entries (a list of dicts keyed by lowercased field
names plus ENTRYTYPE and ID).
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

import bibtexparser
import pytest


# ── Paths ──

# This test file lives at: contracts/scripts/tests/test_references_bib.py
# The contracts/ directory is two parents up from the test file's parent.
CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[2]
REFERENCES_BIB_PATH: Final[Path] = (
    CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "references.bib"
)


# ── Required entries (38 total: 35 original + 2 Colombian-canon + 1 KPSS) ──

# Each tuple is (citation_key, human_readable_description). The description
# is used only in failure messages; the key is the assertion target.
#
# 2026-04-18 addition (Task 15 three-way review gate citation integrity fix):
#   anzoateguiGalvis2019comunicacion + galvisOliveiraAnzoategui2017anuncios
# are the web-verified Colombian-literature anchors for Decision #6
# (BanRep rate surprise event-study ΔIBR methodology). Added after Reality
# Checker flagged the mis-attributed "Uribe-Gil & Galvis-Ciro 2022 BIS WP
# 1022" citation in NB1 cells 73/75 Decision #6 prose; see research doc
# .scratch/2026-04-18-banrep-rate-surprise-methodology-research.md §0
# (Amendment) for full audit trail.
#
# 2026-04-18 addition (Task 15 Model QA MEDIUM follow-up for Decision #11):
#   cavaliereTaylor2005wildKPSS (Econometric Theory 21:6, 1112-1129,
# DOI 10.1017/S0266466605050553) is the canonical technical source for the
# KPSS over-rejection behavior under time-varying second moments cited in
# NB1 cell 105 (Decision #11 stationarity policy lock prose). Added after
# Model QA flagged the "documented small-sample behavior" attribution as
# underspecified without a specific reference.
REQUIRED_ENTRIES: Final[tuple[tuple[str, str], ...]] = (
    ("andersen2001distribution", "Andersen-Bollerslev-Diebold-Ebens 2001 JFE realized vol"),
    ("andersen2003micro", "Andersen-Bollerslev-Diebold-Vega 2003 AER micro macro announcements"),
    ("andrews1991heteroskedasticity", "Andrews 1991 Econometrica HAC consistency"),
    ("ang2006crosssection", "Ang-Hodrick-Xing-Zhang 2006 JFE cross-section of vol"),
    ("ankelPeters2024protocol", "Ankel-Peters-Brodeur et al. 2024 I4R robustness protocol"),
    ("anzoateguiGalvis2019comunicacion", "Anzoátegui-Zapata-Galvis-Ciro 2019 Cuadernos de Economía 38(77) — Decision #6 secondary Colombian anchor (event-study ΔIBR-1m on public debt)"),
    ("baiPerron1998estimating", "Bai-Perron 1998 Econometrica structural changes"),
    ("baiPerron2003computation", "Bai-Perron 2003 JAE computation structural change"),
    ("balduzzi2001economic", "Balduzzi-Elton-Green 2001 JFQA news and bond prices"),
    ("baroneAdesi2008filtered", "Barone-Adesi-Engle-Mancini 2008 RFS GARCH-FHS option pricing"),
    ("belsley1980regression", "Belsley-Kuh-Welsch 1980 Wiley regression diagnostics (VIF)"),
    ("bollerslev1986generalized", "Bollerslev 1986 JE GARCH"),
    ("bollerslevWooldridge1992qmle", "Bollerslev-Wooldridge 1992 Econometric Reviews QMLE"),
    ("breuschPagan1979heteroscedasticity", "Breusch-Pagan 1979 Econometrica heteroscedasticity"),
    ("campbell1997econometrics", "Campbell-Lo-MacKinlay 1997 Princeton textbook"),
    ("cavaliereTaylor2005wildKPSS", "Cavaliere-Taylor 2005 Econometric Theory 21(6):1112-1129 — KPSS stationarity under time-varying second moments (Decision #11 attribution)"),
    ("chow1960tests", "Chow 1960 Econometrica equality of coefficients"),
    ("conover1981comparative", "Conover-Johnson-Johnson 1981 Technometrics Brown-Forsythe Levene"),
    ("conrad2025longterm", "Conrad-Schoelkopf-Tushteva 2025 JE long-term vol sensitivity (SSRN 4632733)"),
    ("durbinWatson1951serial", "Durbin-Watson 1951 Biometrika serial correlation II"),
    ("edererNordhaus2020wti", "Ederer-Nordhaus 2020 Energy Economics WTI negative price"),
    ("elliott1996efficient", "Elliott-Rothenberg-Stock 1996 Econometrica DF-GLS"),
    ("engleRangel2008spline", "Engle-Rangel 2008 RFS Spline-GARCH"),
    ("fuentes2014bis462", "Fuentes-Pincheira-Julio-Rincón et al. 2014 BIS WP 462"),
    ("galvisOliveiraAnzoategui2017anuncios", "Galvis-Ciro-Oliveira-Anzoátegui 2017 Lecturas de Economía 87 — Decision #6 primary Colombian anchor (event-study ΔIBR-1m on COP/USD FX volatility)"),
    ("hanKristensen2014garch", "Han-Kristensen 2014 JBES GARCH-X QMLE asymptotics"),
    ("hansenLunde2005forecast", "Hansen-Lunde 2005 JAE anything beat GARCH(1,1)"),
    ("hestonNandi2000closed", "Heston-Nandi 2000 RFS closed-form GARCH option"),
    ("jarqueBera1987normality", "Jarque-Bera 1987 ISR normality test"),
    ("kwiatkowski1992kpss", "Kwiatkowski-Phillips-Schmidt-Shin 1992 JE KPSS stationarity"),
    ("levene1960robust", "Levene 1960 Stanford Hotelling volume — robust equality of variances"),
    ("ljungBox1978measure", "Ljung-Box 1978 Biometrika lack of fit"),
    ("mincerZarnowitz1969evaluation", "Mincer-Zarnowitz 1969 NBER forecast evaluation"),
    ("neweyWest1987simple", "Newey-West 1987 Econometrica HAC covariance"),
    ("politisRomano1994stationary", "Politis-Romano 1994 JASA stationary bootstrap"),
    ("rinconTorres2021interdependence", "Rincón-Torres-Rojas-Silva-Julio-Román 2021 BanRep Borrador 1171"),
    ("simonsohn2020specification", "Simonsohn-Simmons-Nelson 2020 NHB specification curve"),
    ("wilsonHilferty1931chisquare", "Wilson-Hilferty 1931 PNAS chi-square distribution"),
)


# ── Helpers ──

def _load_database() -> bibtexparser.bibdatabase.BibDatabase:
    """Parse references.bib once and return the BibDatabase object.

    The test asserts file existence before parsing so any bibtexparser error
    surfaces as a real parse failure, not a missing-file failure.
    """
    assert REFERENCES_BIB_PATH.is_file(), (
        f"references.bib missing at {REFERENCES_BIB_PATH}"
    )
    with REFERENCES_BIB_PATH.open("r", encoding="utf-8") as fh:
        return bibtexparser.load(fh)


def _entries_by_key() -> dict[str, dict[str, str]]:
    """Return a dict keyed by citation key for fast lookups in the tests."""
    db = _load_database()
    return {entry["ID"]: entry for entry in db.entries}


# ── Tests ──

def test_references_bib_file_exists() -> None:
    """references.bib exists at the Colombia/ notebook folder root."""
    assert REFERENCES_BIB_PATH.is_file(), (
        f"Missing file: {REFERENCES_BIB_PATH}"
    )


def test_references_bib_parses_with_bibtexparser() -> None:
    """The file is syntactically valid BibTeX (parses without error)."""
    db = _load_database()
    assert db.entries, "references.bib parsed but contains zero entries"


def test_references_bib_has_all_38_required_keys() -> None:
    """Every required entry is present. Failure message names the missing keys."""
    entries = _entries_by_key()
    missing = [
        f"{key} ({desc})"
        for key, desc in REQUIRED_ENTRIES
        if key not in entries
    ]
    assert not missing, (
        f"Missing BibTeX entries ({len(missing)} of {len(REQUIRED_ENTRIES)}): "
        + "; ".join(missing)
    )


def test_references_bib_entry_count_matches_required() -> None:
    """Exactly the 38 required entries are present (no extras, no omissions)."""
    entries = _entries_by_key()
    required_keys = {key for key, _ in REQUIRED_ENTRIES}
    assert set(entries) == required_keys, (
        "BibTeX key set does not match required set. "
        f"Extra: {sorted(set(entries) - required_keys)}. "
        f"Missing: {sorted(required_keys - set(entries))}."
    )


@pytest.mark.parametrize("key,description", REQUIRED_ENTRIES)
def test_entry_has_non_empty_journal_or_booktitle(
    key: str, description: str
) -> None:
    """Each entry carries a non-empty venue-equivalent field.

    BibTeX entry-types have different canonical venue fields:
      * @article:      journal
      * @incollection: booktitle
      * @book:         publisher (no journal/booktitle)
      * @techreport:   institution (no journal/booktitle)

    Per the plan spec, every entry must have a populated venue; this test
    dispatches on ENTRYTYPE and enforces the right field for each type.
    """
    entries = _entries_by_key()
    if key not in entries:
        pytest.skip(f"Entry {key} not present — covered by key-existence test")
    entry = entries[key]
    journal = entry.get("journal", "").strip()
    booktitle = entry.get("booktitle", "").strip()
    publisher = entry.get("publisher", "").strip()
    institution = entry.get("institution", "").strip()
    entrytype = entry.get("ENTRYTYPE", "").lower()

    if entrytype == "book":
        assert publisher, (
            f"Entry {key} ({description}) is @book but has empty "
            f"publisher field"
        )
    elif entrytype == "techreport":
        assert institution, (
            f"Entry {key} ({description}) is @techreport but has empty "
            f"institution field"
        )
    else:
        assert journal or booktitle, (
            f"Entry {key} ({description}) has empty journal and empty "
            f"booktitle (entrytype={entrytype!r})"
        )


def test_hanKristensen_journal_is_jbes() -> None:
    """Han-Kristensen 2014 must be JBES, not Journal of Econometrics.

    This was an explicit correction applied in plan revision 2. The paper
    is: "Asymptotic Theory for the QMLE in GARCH-X Models With Stationary
    and Nonstationary Covariates", Journal of Business & Economic
    Statistics, 32(3), 416-429, DOI 10.1080/07350015.2014.897954.
    """
    entries = _entries_by_key()
    assert "hanKristensen2014garch" in entries, (
        "Entry hanKristensen2014garch missing"
    )
    journal = entries["hanKristensen2014garch"].get("journal", "").strip()
    assert journal == r"Journal of Business {\&} Economic Statistics", (
        r"Han-Kristensen journal must be exactly 'Journal of Business {\&} "
        f"Economic Statistics' (plan rev 2 correction + LaTeX-safe escape), "
        f"got: {journal!r}"
    )


@pytest.mark.parametrize("key,description", REQUIRED_ENTRIES)
def test_entry_has_doi_or_url(key: str, description: str) -> None:
    """Every entry carries either a `doi` or a `url` so it is verifiable.

    Fabricated DOIs are forbidden; for pre-DOI or non-DOI sources
    (working papers, Stanford volumes, PNAS 1931) a `url` field is required.
    """
    entries = _entries_by_key()
    if key not in entries:
        pytest.skip(f"Entry {key} not present — covered by key-existence test")
    entry = entries[key]
    doi = entry.get("doi", "").strip()
    url = entry.get("url", "").strip()
    assert doi or url, (
        f"Entry {key} ({description}) has neither a doi nor a url field"
    )


@pytest.mark.parametrize("key,description", REQUIRED_ENTRIES)
def test_entry_has_author_title_year(key: str, description: str) -> None:
    """Every entry carries non-empty author, title, and year fields."""
    entries = _entries_by_key()
    if key not in entries:
        pytest.skip(f"Entry {key} not present — covered by key-existence test")
    entry = entries[key]
    author = entry.get("author", "").strip()
    title = entry.get("title", "").strip()
    year = entry.get("year", "").strip()
    missing = []
    if not author:
        missing.append("author")
    if not title:
        missing.append("title")
    if not year:
        missing.append("year")
    assert not missing, (
        f"Entry {key} ({description}) missing required field(s): "
        + ", ".join(missing)
    )
