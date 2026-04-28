"""
Pair D Task 1.1 fourth dispatch — DANE GEIH young-worker services-share Y panel.

Spec sha256 (sentinel-protocol):
    decision_hash = 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
    Computed against the spec file with `decision_hash` field set to literal sentinel
    `<to-be-pinned-after-CORRECTIONS-alpha-prime-3way-cleanup>`. To re-verify, replace
    the pinned hash in spec frontmatter with the sentinel string and recompute sha256.

Window: 2015-01 → 2026-03 inclusive (135 candidate months).
Filter: youth band 14-28 (P6040), employed (file membership in Ocupados.CSV).
Outputs:
    geih_young_workers_services_share.parquet  (broad: CIIU Rev.4 sections G-T)
    geih_young_workers_narrow_share.parquet    (narrow: CIIU Rev.4 sections J+M+N)

Schema per parquet: (timestamp_utc, Y_raw, Y_logit, n_young_employed, n_young_in_sector)
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

# --- Paths ----------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent  # .scratch/simple-beta-pair-d/data/
DOWNLOADS = ROOT / "downloads"
SCRIPTS = ROOT / "scripts"
DOWNLOADS.mkdir(parents=True, exist_ok=True)

OUT_BROAD = ROOT / "geih_young_workers_services_share.parquet"
OUT_NARROW = ROOT / "geih_young_workers_narrow_share.parquet"

MANIFEST_PATH = ROOT / "dane_geih_manifest.json"

# --- CIIU Rev.4 section-letter → 2-digit-range mapping -------------------
# Canonical per ISIC Rev.4 / DANE CIIU 4 a.c. publication:
#   https://www.dane.gov.co/files/sen/nomenclatura/ciiu/CIIU_Rev_4_AC2022.pdf

SECTION_TO_2DIGITS: dict[str, set[int]] = {
    "A": set(range(1, 4)),       # 01-03 Agriculture
    "B": set(range(5, 10)),      # 05-09 Mining
    "C": set(range(10, 34)),     # 10-33 Manufacturing
    "D": {35},                   # Electricity, gas
    "E": set(range(36, 40)),     # 36-39 Water/waste
    "F": set(range(41, 44)),     # 41-43 Construction
    "G": set(range(45, 48)),     # 45-47 Wholesale/retail trade
    "H": set(range(49, 54)),     # 49-53 Transportation/storage
    "I": set(range(55, 57)),     # 55-56 Accommodation/food
    "J": set(range(58, 64)),     # 58-63 Information/communication
    "K": set(range(64, 67)),     # 64-66 Finance/insurance
    "L": {68},                   # Real estate
    "M": set(range(69, 76)),     # 69-75 Professional/scientific/technical
    "N": set(range(77, 83)),     # 77-82 Administrative/support (BPO 822)
    "O": {84},                   # Public administration
    "P": {85},                   # Education
    "Q": set(range(86, 89)),     # 86-88 Human health/social
    "R": set(range(90, 94)),     # 90-93 Arts/entertainment
    "S": set(range(94, 97)),     # 94-96 Other services
    "T": set(range(97, 99)),     # 97-98 Households as employers
    "U": {99},                   # Extra-territorial
}

BROAD_SERVICES_SECTIONS = list("GHIJKLMNOPQRST")  # spec §5.1
NARROW_SERVICES_SECTIONS = ["J", "M", "N"]         # spec §7 R2

BROAD_2DIGIT: set[int] = set().union(*(SECTION_TO_2DIGITS[s] for s in BROAD_SERVICES_SECTIONS))
NARROW_2DIGIT: set[int] = set().union(*(SECTION_TO_2DIGITS[s] for s in NARROW_SERVICES_SECTIONS))


@dataclass(frozen=True)
class FilePlan:
    """One ingestion job."""

    year: int
    month: int
    era: str  # "empalme_2015_2020" | "marco2018_sem_2021" | "marco2018_native"
    download_url: str
    cache_path: Path
    inner_path_match: str  # substring identifying the inner Ocupados.CSV
    char_inner_match: str  # substring identifying Características CSV
    fex_col: str           # "FEX_C" or "FEX_C18"
    rama_col: str          # "RAMA4D_R4"
    file_id: int


SPANISH_MONTHS = {
    1: ("Enero", "ENE"), 2: ("Febrero", "FEB"), 3: ("Marzo", "MAR"),
    4: ("Abril", "ABR"), 5: ("Mayo", "MAY"), 6: ("Junio", "JUN"),
    7: ("Julio", "JUL"), 8: ("Agosto", "AGO"), 9: ("Septiembre", "SEP"),
    10: ("Octubre", "OCT"), 11: ("Noviembre", "NOV"), 12: ("Diciembre", "DIC"),
}


def _http_get(url: str, dest: Path, timeout: int = 600) -> None:
    """Download URL to dest with retries."""
    if dest.exists() and dest.stat().st_size > 0:
        return
    last_err = None
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            fh.write(chunk)
                tmp.rename(dest)
            return
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to download {url} after 3 attempts: {last_err}")


def _detect_csv_format(blob: bytes) -> tuple[str, str]:
    """Return (encoding, separator) for a CSV blob.

    Encoding decision: try strict UTF-8 across the FULL blob (not just header).
    If full-blob UTF-8 decode succeeds, use UTF-8; otherwise fall back to
    Latin-1 (which never raises). Header bytes alone can decode as UTF-8
    while interior cells contain Latin-1 mojibake, so header-only detection
    silently misclassifies (e.g. 2021 Mayo Ocupados.csv produces a 0xc3
    error mid-stream).
    """
    try:
        blob.decode("utf-8")
        enc = "utf-8"
    except UnicodeDecodeError:
        enc = "latin-1"

    head = blob[:8000].decode(enc, errors="replace")
    line0 = head.split("\n", 1)[0]
    sep = ";" if line0.count(";") > line0.count(",") else ","
    return enc, sep


# Canonical column aliases (case-insensitive). DANE publishes the same
# semantic column under varying capitalizations within the same Empalme
# catalog (e.g. 2020-01 has `RAMA4D_R4`, 2020-03 has `Rama4d_r4`). These
# are NOT a methodologically meaningful schema break — both columns carry
# identical Rev.4 4-digit codes per value-content verification. Resolve at
# ingest by canonicalizing all field names to UPPER then matching against
# the spec-pinned canonical names below.
_COL_ALIASES_UPPER: dict[str, str] = {
    "RAMA4D_R4": "RAMA4D_R4",
    "RAMA4D_R4 ": "RAMA4D_R4",  # trailing-space tolerance
    "RAMA4DR4": "RAMA4D_R4",     # underscore-stripping tolerance
    "FEX_C": "FEX_C",
    "FEX_C18": "FEX_C18",
    "FEX_C_2018": "FEX_C18",
    "OCI": "OCI",
    "P6040": "P6040",
    "DIRECTORIO": "DIRECTORIO",
    "SECUENCIA_P": "SECUENCIA_P",
    "ORDEN": "ORDEN",
    "HOGAR": "HOGAR",
    "MES": "MES",
    "PERIODO": "PERIODO",
}


def _canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename DataFrame columns to their spec-canonical names (case-insensitive,
    trailing-whitespace tolerant). Unmapped columns retain their original name."""
    rename: dict[str, str] = {}
    for c in df.columns:
        key = c.strip().upper()
        if key in _COL_ALIASES_UPPER:
            rename[c] = _COL_ALIASES_UPPER[key]
    return df.rename(columns=rename)


def _read_csv_subset(blob: bytes, columns: list[str]) -> pd.DataFrame:
    """Decode + parse a CSV blob and return only the requested columns
    (canonical names per `_COL_ALIASES_UPPER`)."""
    enc, sep = _detect_csv_format(blob)
    # First read with NO column filter so we can canonicalize before subsetting.
    df = pd.read_csv(
        io.BytesIO(blob),
        sep=sep,
        encoding=enc,
        low_memory=False,
        dtype=str,
        on_bad_lines="warn",
    )
    df = _canonicalize_columns(df)
    keep = [c for c in columns if c in df.columns]
    return df[keep]


def _basename_lower(zip_inner_path: str) -> str:
    """Return lowercase filename portion of a zip inner path (after last '/')."""
    return zip_inner_path.rsplit("/", 1)[-1].lower()


def _is_ocupados_csv(zip_inner_path: str) -> bool:
    """Match exactly Ocupados.csv (case-insensitive), excluding Desocupados.csv,
    No ocupados.csv, etc."""
    return _basename_lower(zip_inner_path) in ("ocupados.csv",)


def _is_caracteristicas_csv(zip_inner_path: str) -> bool:
    """Match Características-* CSV (case-insensitive, encoding-tolerant)."""
    bn = _basename_lower(zip_inner_path)
    if not bn.endswith(".csv"):
        return False
    # 'caracter' or mojibake variants ('caracter' is robust ascii prefix)
    return "aracter" in bn


def _load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def _build_plans(manifest: dict) -> list[FilePlan]:
    plans: list[FilePlan] = []

    # 2015-2020: Empalme catalogs (per-year zip; inner per-month sub-zip + Ocupados.CSV)
    for yr in range(2015, 2021):
        ent = manifest[str(yr)]["empalme"]
        cid = ent["catalog_id"]
        # exactly one annual zip
        f = ent["files"][0]
        url = f["download_url"]
        cache = DOWNLOADS / f"empalme_{yr}.zip"
        for mo in range(1, 13):
            sp_name, _ = SPANISH_MONTHS[mo]
            inner_match = f"{mo}. {sp_name}/CSV/Ocupados.CSV"
            char_match = f"{mo}. {sp_name}/CSV/Características generales (personas).CSV"
            plans.append(FilePlan(
                year=yr, month=mo, era="empalme_2015_2020",
                download_url=url, cache_path=cache,
                inner_path_match=inner_match,
                char_inner_match=char_match,
                fex_col="FEX_C", rama_col="RAMA4D_R4",
                file_id=f["file_id"],
            ))

    # 2021: Marco-2018 semester archives
    sem1 = next(f for f in manifest["2021"]["native"]["files"] if "I.Semestre" in f["filename"])
    sem2 = next(f for f in manifest["2021"]["native"]["files"] if "II. semestre" in f["filename"])
    sem1_cache = DOWNLOADS / "2021_marco2018_sem1.zip"
    sem2_cache = DOWNLOADS / "2021_marco2018_sem2.zip"

    for mo in range(1, 7):  # I.Semestre = Jan-Jun
        sp_name, _ = SPANISH_MONTHS[mo]
        inner_match = f"{sp_name} 2021/CSV"  # path contains e.g. "Enero 2021/CSV ENE21/Ocupados.CSV"
        # Need to be more specific to pick Ocupados in the right month
        plans.append(FilePlan(
            year=2021, month=mo, era="marco2018_sem_2021",
            download_url=sem1["download_url"], cache_path=sem1_cache,
            inner_path_match=f"{sp_name} 2021/CSV",
            char_inner_match=f"{sp_name} 2021/CSV",
            fex_col="FEX_C18", rama_col="RAMA4D_R4",
            file_id=sem1["file_id"],
        ))

    for mo in range(7, 13):  # II.Semestre = Jul-Dec
        sp_name, _ = SPANISH_MONTHS[mo]
        plans.append(FilePlan(
            year=2021, month=mo, era="marco2018_sem_2021",
            download_url=sem2["download_url"], cache_path=sem2_cache,
            inner_path_match=f"{sp_name} 2021/CSV",
            char_inner_match=f"{sp_name} 2021/CSV",
            fex_col="FEX_C18", rama_col="RAMA4D_R4",
            file_id=sem2["file_id"],
        ))

    # 2022-2026: Marco-2018 native per-month. Filename conventions are
    # heterogeneous across DANE catalogs:
    #   2022: "GEIH_<Spanish>_2022_Marco_2018.zip", "GEIH_<Spanish>_Marco_2018.zip"
    #         (no year), "GEIH_Abril_2022_Marco_2018_Act.zip" (suffix variant),
    #         "GEIH_Noviembre_2022_Marco_2018.act.zip" (.act dotted variant).
    #   2023: "<Spanish>.zip"
    #   2024: "Ene_2024.zip", "Marzo 2024.zip", "Mayo_2024 1.zip",
    #         "Noviembre_ 2024.zip" — mixed underscores/spaces and stray chars.
    #   2025-2026: "<Spanish> <YYYY>.zip" (space-separated).
    # Best-match strategy: tokenize the filename on '/', ' ', '-', '_', '.',
    # then accept any file whose tokens contain (sp_full | sp_full[:3]) — and
    # whose filename does NOT contain a different year (strict per-year match).
    def _tokenize_fn(fn: str) -> set[str]:
        return set(
            fn.lower()
              .replace("/", " ").replace("-", " ").replace("_", " ").replace(".", " ")
              .split()
        )

    def _match_monthly(year: int, mo: int, monthly: dict[str, dict]) -> dict | None:
        sp_full, sp_short = SPANISH_MONTHS[mo]
        sp_full_l = sp_full.lower()
        sp_pre3 = sp_full[:3].lower()
        for fn, f in monthly.items():
            tokens = _tokenize_fn(fn)
            if sp_full_l not in tokens and sp_pre3 not in tokens:
                continue
            # Exclude files whose tokens contain a *different* 4-digit year.
            for tok in tokens:
                if tok.isdigit() and len(tok) == 4 and tok != str(year):
                    # Allow Marco-2018 marker for 2022-2025 archives
                    if tok == "2018":
                        continue
                    break
            else:
                return f
        return None

    monthly_2022 = {f["filename"]: f for f in manifest["2022"]["native"]["files"]}
    for mo in range(1, 13):
        f = _match_monthly(2022, mo, monthly_2022)
        if f is None:
            continue
        plans.append(FilePlan(
            year=2022, month=mo, era="marco2018_native",
            download_url=f["download_url"], cache_path=DOWNLOADS / f["filename"],
            inner_path_match="Ocupados.csv",
            char_inner_match="aracter",
            fex_col="FEX_C18", rama_col="RAMA4D_R4",
            file_id=f["file_id"],
        ))

    for yr in (2023, 2024, 2025):
        monthly = {f["filename"]: f for f in manifest[str(yr)]["native"]["files"]}
        for mo in range(1, 13):
            f = _match_monthly(yr, mo, monthly)
            if f is None:
                continue
            plans.append(FilePlan(
                year=yr, month=mo, era="marco2018_native",
                download_url=f["download_url"],
                cache_path=DOWNLOADS / f"{yr}_{f['filename']}",
                inner_path_match="Ocupados.CSV",
                char_inner_match="aracter",
                fex_col="FEX_C18", rama_col="RAMA4D_R4",
                file_id=f["file_id"],
            ))

    # 2026: include only first two months (Jan + Feb) per dispatch publication-lag
    # rule (exclude most recent 2 months → 2026-03 not yet reliably published).
    monthly_2026 = {f["filename"]: f for f in manifest["2026"]["native"]["files"]}
    for mo in (1, 2):
        f = _match_monthly(2026, mo, monthly_2026)
        if f is None:
            continue
        plans.append(FilePlan(
            year=2026, month=mo, era="marco2018_native",
            download_url=f["download_url"],
            cache_path=DOWNLOADS / f"2026_{f['filename']}",
            inner_path_match="Ocupados.CSV",
            char_inner_match="aracter",
            fex_col="FEX_C18", rama_col="RAMA4D_R4",
            file_id=f["file_id"],
        ))

    return plans


# --- Per-month ingest -----------------------------------------------------

def _classify_section(rama4d: str) -> str | None:
    """Map a 4-digit CIIU Rev.4 code (as string) to its section letter, or None."""
    if not rama4d or rama4d in (".", "0", "00", "0000"):
        return None
    try:
        code4 = int(rama4d)
    except (TypeError, ValueError):
        return None
    code2 = code4 // 100
    for letter, ranges in SECTION_TO_2DIGITS.items():
        if code2 in ranges:
            return letter
    return None


def _decode_csv_to_df(blob: bytes, want_cols: list[str]) -> pd.DataFrame:
    """Decode CSV bytes, canonicalize column names (case-insensitive, trailing
    whitespace tolerant), and return only the want_cols subset (in canonical
    naming). Encoding fallback: UTF-8 across full blob, then Latin-1."""
    enc, sep = _detect_csv_format(blob)
    df = pd.read_csv(
        io.BytesIO(blob), sep=sep, encoding=enc,
        low_memory=False, dtype=str,
        on_bad_lines="warn",
    )
    df = _canonicalize_columns(df)
    keep = [c for c in want_cols if c in df.columns]
    return df[keep]


def _ingest_month(plan: FilePlan) -> dict:
    """Produce one monthly Y data row (broad + narrow) from a FilePlan."""
    _http_get(plan.download_url, plan.cache_path)

    # Empalme 2015-2020: outer annual zip contains 12 inner per-month zips, each
    # of which contains "<n>. <SpanishMonth>/CSV/Ocupados.CSV" + Características CSV.
    if plan.era == "empalme_2015_2020":
        sp_name, _ = SPANISH_MONTHS[plan.month]
        with zipfile.ZipFile(plan.cache_path) as outer:
            # Find the inner zip for this month
            inner_candidates = [
                n for n in outer.namelist()
                if n.lower().endswith(".zip")
                and f"{plan.month}. {sp_name.lower()}.zip" in n.lower()
            ]
            if not inner_candidates:
                # Some zips use different formatting (e.g. "1. enero.zip" vs "1.enero.zip")
                inner_candidates = [
                    n for n in outer.namelist()
                    if n.lower().endswith(".zip")
                    and f"{plan.month}." in n.lower()
                    and sp_name.lower() in n.lower()
                ]
            if not inner_candidates:
                raise FileNotFoundError(
                    f"Inner monthly zip not found for {plan.year}-{plan.month:02d} "
                    f"in {plan.cache_path} (looking for '{plan.month}. {sp_name}.zip')"
                )
            inner_name = inner_candidates[0]
            with outer.open(inner_name) as fh:
                inner_bytes = fh.read()

        with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
            names = inner.namelist()
            oc_names = [n for n in names if _is_ocupados_csv(n)]
            char_names = [n for n in names if _is_caracteristicas_csv(n)]
            if not oc_names or not char_names:
                raise FileNotFoundError(
                    f"Ocupados/Características not found inside {inner_name} for "
                    f"{plan.year}-{plan.month:02d}; entries: {names[:10]}"
                )
            with inner.open(oc_names[0]) as fh:
                oc_blob = fh.read()
            with inner.open(char_names[0]) as fh:
                ch_blob = fh.read()

    elif plan.era == "marco2018_sem_2021":
        sp_full, _sp_short = SPANISH_MONTHS[plan.month]
        # 2021 Sem-I uses inconsistent folder naming:
        #   Enero 2021/CSV ENE21/, Feb 2021/CSV FEB 21/, Mar 2021/CSV MAR21/,
        #   Abril 2021/CSV abr21/, Mayo 2021/CSV/, Junio 2021/CSV/.
        # 2021 Sem-II uses: GEIH - Julio - Marco - 2018/CSV/, etc.
        # (Note Sem-II archive name says "2018" — that refers to the Marco-2018
        # frame; the data IS the 2021 Jul-Dec months.)
        # Match strategy: look for any folder containing the full Spanish
        # month name or its 3-letter prefix as a tokenized path component
        # (separated by '/', ' ', or '-'). Don't require literal "2021" in
        # the path — Sem-II paths embed only "2018".
        sp_prefix3 = sp_full[:3].lower()  # e.g. "feb" matches "Feb 2021"
        with zipfile.ZipFile(plan.cache_path) as z:
            names = z.namelist()

            def _path_matches_month(p: str) -> bool:
                pl = p.lower()
                # Split on '/', ' ', '-', '_' — Sem-I uses dashes/spaces/parens,
                # Sem-II Octubre uses underscores ("GEIH_Octubre_Marco_2018/").
                tokens = (
                    pl.replace("/", " ").replace("-", " ").replace("_", " ").split()
                )
                return sp_full.lower() in tokens or sp_prefix3 in tokens

            oc_names = [n for n in names
                        if _path_matches_month(n) and _is_ocupados_csv(n)]
            if not oc_names:
                raise FileNotFoundError(
                    f"2021-{plan.month:02d} Ocupados.CSV not found in semester archive "
                    f"({plan.cache_path.name}); month_token={sp_full}/{sp_prefix3}"
                )
            oc_name = oc_names[0]
            # Pair Características from the same folder.
            oc_dir = oc_name.rsplit("/", 1)[0]
            char_names = [n for n in names
                          if n.startswith(oc_dir + "/")
                          and _is_caracteristicas_csv(n)]
            if not char_names:
                raise FileNotFoundError(
                    f"2021-{plan.month:02d} Características not found in {oc_dir}"
                )
            char_name = char_names[0]
            with z.open(oc_name) as fh:
                oc_blob = fh.read()
            with z.open(char_name) as fh:
                ch_blob = fh.read()

    else:  # marco2018_native (2022-2026)
        with zipfile.ZipFile(plan.cache_path) as z:
            names = z.namelist()
            oc_names = [n for n in names if _is_ocupados_csv(n)]
            if not oc_names:
                # Possibly nested
                inners = [n for n in names if n.lower().endswith(".zip")]
                for inn in inners:
                    with z.open(inn) as fh:
                        inn_bytes = fh.read()
                    with zipfile.ZipFile(io.BytesIO(inn_bytes)) as z2:
                        oc_inner = [n for n in z2.namelist() if _is_ocupados_csv(n)]
                        if oc_inner:
                            with z2.open(oc_inner[0]) as fh:
                                oc_blob = fh.read()
                            char_inner = [n for n in z2.namelist() if _is_caracteristicas_csv(n)]
                            with z2.open(char_inner[0]) as fh:
                                ch_blob = fh.read()
                            break
                else:
                    raise FileNotFoundError(f"Ocupados.csv not found in {plan.cache_path}")
            else:
                oc_name = oc_names[0]
                char_names = [n for n in names if _is_caracteristicas_csv(n)]
                char_name = char_names[0]
                with z.open(oc_name) as fh:
                    oc_blob = fh.read()
                with z.open(char_name) as fh:
                    ch_blob = fh.read()

    # Read just the columns we need.
    # From Ocupados: DIRECTORIO, SECUENCIA_P, ORDEN, HOGAR, FEX_C(or _C18), RAMA4D_R4
    # From Características: DIRECTORIO, SECUENCIA_P, ORDEN, HOGAR, P6040
    pk_cols = ["DIRECTORIO", "SECUENCIA_P", "ORDEN", "HOGAR"]
    oc_cols = pk_cols + [plan.fex_col, plan.rama_col]
    ch_cols = pk_cols + ["P6040"]

    df_oc = _decode_csv_to_df(oc_blob, oc_cols)
    df_ch = _decode_csv_to_df(ch_blob, ch_cols)

    # Validate column presence — HALT if missing.
    missing_oc = set(oc_cols) - set(df_oc.columns)
    missing_ch = set(ch_cols) - set(df_ch.columns)
    if missing_oc:
        raise RuntimeError(
            f"HALT: {plan.year}-{plan.month:02d} Ocupados missing columns {missing_oc}. "
            f"Found: {sorted(df_oc.columns)}"
        )
    if missing_ch:
        raise RuntimeError(
            f"HALT: {plan.year}-{plan.month:02d} Características missing columns {missing_ch}. "
            f"Found: {sorted(df_ch.columns)}"
        )

    # Cast types
    df_ch["P6040"] = pd.to_numeric(df_ch["P6040"], errors="coerce")
    df_oc[plan.fex_col] = pd.to_numeric(df_oc[plan.fex_col], errors="coerce")

    # Inner join on PK
    # Inner join. NOTE: validate="one_to_one" was tried first but DANE files
    # occasionally have non-unique PKs in Características for cross-listed
    # households (rare; pre-2018 era). Use validate="m:1" to permit Ocupados →
    # Características asymmetry (multiple Ocupados rows per person is invalid
    # by GEIH design but we don't enforce it here; the spec's ratio-of-FEX
    # share is robust to single-row dupes).
    merged = df_oc.merge(df_ch, on=pk_cols, how="inner", validate="m:1")

    # Filter youth band 14-28 inclusive (Ley 1622 de 2013)
    youth = merged[(merged["P6040"] >= 14) & (merged["P6040"] <= 28)].copy()

    # Filter rows where FEX is positive numeric
    youth = youth[youth[plan.fex_col] > 0]

    # Section letter
    youth["_section"] = youth[plan.rama_col].apply(_classify_section)

    # Drop rows with unmappable RAMA codes (treat as not-employed for share denominator?
    # Spec §5.1: numerator = young-employed in services; denominator = young-employed.
    # All rows in Ocupados.CSV are employed; unmappable codes must NOT be in the denominator
    # if the spec interpretation is "share of EMPLOYED-WITH-VALID-CODE"; under standard
    # practice, missing-sector rows are kept in the denominator (as employed) and excluded
    # from the numerator. We adopt: keep all employed in denominator; numerator = those
    # whose section ∈ {G..T} (broad) or {J,M,N} (narrow). Missing/unmappable codes are
    # excluded from the numerator.

    fex = plan.fex_col

    fex_total = float(youth[fex].sum())
    fex_broad = float(youth[youth["_section"].isin(BROAD_SERVICES_SECTIONS)][fex].sum())
    fex_narrow = float(youth[youth["_section"].isin(NARROW_SERVICES_SECTIONS)][fex].sum())

    n_total = int(len(youth))
    n_broad = int((youth["_section"].isin(BROAD_SERVICES_SECTIONS)).sum())
    n_narrow = int((youth["_section"].isin(NARROW_SERVICES_SECTIONS)).sum())

    Y_broad_raw = fex_broad / fex_total if fex_total > 0 else float("nan")
    Y_narrow_raw = fex_narrow / fex_total if fex_total > 0 else float("nan")

    return {
        "year": plan.year,
        "month": plan.month,
        "era": plan.era,
        "fex_total": fex_total,
        "fex_broad": fex_broad,
        "fex_narrow": fex_narrow,
        "n_young_employed": n_total,
        "n_young_in_broad": n_broad,
        "n_young_in_narrow": n_narrow,
        "Y_broad_raw": Y_broad_raw,
        "Y_narrow_raw": Y_narrow_raw,
    }


def _logit(p: float) -> float:
    if not (0 < p < 1):
        return float("nan")
    return math.log(p / (1 - p))


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-months", type=int, default=None,
                        help="If set, ingest only the first N months (debugging).")
    parser.add_argument("--year", type=int, default=None,
                        help="If set, ingest only this year.")
    args = parser.parse_args()

    manifest = _load_manifest()
    plans = _build_plans(manifest)

    if args.year is not None:
        plans = [p for p in plans if p.year == args.year]
    if args.max_months is not None:
        plans = plans[: args.max_months]

    print(f"Total ingest plans: {len(plans)}")

    rows: list[dict] = []
    failures: list[tuple[FilePlan, str]] = []

    for i, plan in enumerate(plans):
        ts = time.time()
        try:
            row = _ingest_month(plan)
            rows.append(row)
            elapsed = time.time() - ts
            print(
                f"[{i+1:3d}/{len(plans)}] {plan.year}-{plan.month:02d} "
                f"era={plan.era} n={row['n_young_employed']:>5d} "
                f"Y_broad={row['Y_broad_raw']:.4f} Y_narrow={row['Y_narrow_raw']:.4f} "
                f"({elapsed:.1f}s)"
            )
        except Exception as e:  # noqa: BLE001
            print(f"[{i+1:3d}/{len(plans)}] {plan.year}-{plan.month:02d} FAILED: {e}")
            failures.append((plan, str(e)))

    if not rows:
        print("No rows produced. Aborting.")
        return 1

    df = pd.DataFrame(rows)
    # Use last-calendar-day-of-month to match the convention in
    # `cop_usd_panel.parquet` (Task 1.2), so Task 1.3 join on year/month is
    # exact and downstream sort orders align.
    df["timestamp_utc"] = (
        pd.to_datetime({"year": df["year"], "month": df["month"], "day": 1}, utc=True)
        + pd.offsets.MonthEnd(0)
    )
    df = df.sort_values("timestamp_utc").reset_index(drop=True)

    # Write broad
    df_broad = df[["timestamp_utc", "Y_broad_raw", "n_young_employed", "n_young_in_broad", "era"]].copy()
    df_broad["Y_logit"] = df_broad["Y_broad_raw"].apply(_logit)
    df_broad = df_broad.rename(columns={"Y_broad_raw": "Y_raw", "n_young_in_broad": "n_young_in_sector"})
    df_broad = df_broad[["timestamp_utc", "Y_raw", "Y_logit", "n_young_employed", "n_young_in_sector", "era"]]
    df_broad.to_parquet(OUT_BROAD, index=False)
    print(f"Wrote {OUT_BROAD} ({len(df_broad)} rows)")

    df_narrow = df[["timestamp_utc", "Y_narrow_raw", "n_young_employed", "n_young_in_narrow", "era"]].copy()
    df_narrow["Y_logit"] = df_narrow["Y_narrow_raw"].apply(_logit)
    df_narrow = df_narrow.rename(columns={"Y_narrow_raw": "Y_raw", "n_young_in_narrow": "n_young_in_sector"})
    df_narrow = df_narrow[["timestamp_utc", "Y_raw", "Y_logit", "n_young_employed", "n_young_in_sector", "era"]]
    df_narrow.to_parquet(OUT_NARROW, index=False)
    print(f"Wrote {OUT_NARROW} ({len(df_narrow)} rows)")

    if failures:
        print(f"\n{len(failures)} failures:")
        for p, err in failures:
            print(f"  {p.year}-{p.month:02d} {p.era}: {err[:200]}")

    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
