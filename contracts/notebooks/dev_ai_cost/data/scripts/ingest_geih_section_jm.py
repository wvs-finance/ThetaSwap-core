"""
Dev-AI-cost iteration Stage-1 Task 1.1 — DANE GEIH Section J + Section M young-worker shares.

Plan: contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md (v1.1)
Plan sha256: 6da9cce597abb7ed9da2a8f82700f502c04a0ba25d315d05c3085f7ebfe1f86b
Spec: contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md (v1.0.1)
Spec decision_hash: 456ba39e188d00bb17471359a5803d6aa8a40de3b3788f17294bab828a968204

Window: 2015-01 → 2026-03 inclusive (one-month tolerance for end-of-window publication-lag drop).
Filter: youth band 14-28 (P6040, Ley 1622 de 2013), employed (file membership in Ocupados.CSV).
Universe: national aggregate (Cabecera + Resto summed; GEIH micro-data does NOT segment by zone).

Outputs:
    geih_young_workers_section_j_share.parquet  (Y_p, primary; CIIU Rev.4 Section J)
    geih_young_workers_section_m_share.parquet  (Y_s2, sensitivity; CIIU Rev.4 Section M)

Schema per parquet: (year_month, raw_share, logit_share, cell_count, FEX_total)
    where:
      - year_month     = pandas Timestamp at month-end UTC (matches cop_usd_panel.parquet convention)
      - raw_share      = sum(FEX_C[2018]) over young-employed in Section X / sum(FEX_C[2018]) over all young-employed
      - logit_share    = log(raw_share / (1 - raw_share))   (per spec §5.1)
      - cell_count     = integer count of distinct young-employed individuals contributing to NUMERATOR
                         (i.e., young-employed with section letter == X). Diagnostic per plan Task 1.1 Step 5.
      - FEX_total      = sum(FEX_C[2018]) over all young-employed (denominator, in expansion-weighted units)

Pre-flight inheritance (Step 1):
    Per spec §5.1 v1.0.1 line 193 + §6 + Pair D §9.10:
    DANE's `RAMA4D_R4` field is value-content-verified for the entire 2015-01 → 2026-02 Empalme window.
    The Section-letter mapping is unambiguous for every month in this window. Pair D's `step0_schema_findings.json`
    + working pipeline output `geih_young_workers_services_share.parquet` (134 rows, 2015-01 → 2026-02) operationally
    verifies this. We INHERIT that pre-flight verification; the typed exception
    `DevAIStage1RAMA4DRev4ContradictionPathological` is structurally pre-empted by Option-α' window inheritance
    AND empirically pre-empted by Pair D's working pipeline.

Per spec §9.14 (Free-tier methodology only): all data sources are public DANE Microdata portal CSV ZIPs;
no auth, no rate limit, no paid-tier API used.

Empalme application (per spec §6 primary disposition):
    - 2015-01 → 2020-12 (era="empalme_2015_2020"): use `FEX_C` (DANE-published empalme factor; nota técnica)
    - 2021-01 → 2021-12 (era="marco2018_sem_2021"): use `FEX_C18` (Marco-2018 native)
    - 2022-01 → 2026-02 (era="marco2018_native"): use `FEX_C18` (Marco-2018 native)
    Empalme is implicit in the FEX column choice (DANE pre-applied empalme correction in `FEX_C` for the
    2015-2020 catalogs); raw share Y_t is computed BEFORE the logit transform of §5.1.

Reuses Pair D pipeline assets verbatim:
    - Manifest:  contracts/.scratch/simple-beta-pair-d/data/dane_geih_manifest.json
    - Downloads: contracts/.scratch/simple-beta-pair-d/data/downloads/  (~5.4GB cached)
    - Section letter mapping: ISIC Rev.4 / DANE CIIU 4 a.c. publication
      https://www.dane.gov.co/files/sen/nomenclatura/ciiu/CIIU_Rev_4_AC2022.pdf
"""

from __future__ import annotations

import io
import json
import math
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

# --- Paths ----------------------------------------------------------------

DEV_AI_ROOT = Path(__file__).resolve().parent.parent  # .scratch/dev-ai-stage-1/data/
PAIR_D_ROOT = DEV_AI_ROOT.parent.parent / "simple-beta-pair-d" / "data"
DOWNLOADS = PAIR_D_ROOT / "downloads"  # reuse Pair D's cached downloads (free-tier compliant)
MANIFEST_PATH = PAIR_D_ROOT / "dane_geih_manifest.json"

OUT_J = DEV_AI_ROOT / "geih_young_workers_section_j_share.parquet"
OUT_M = DEV_AI_ROOT / "geih_young_workers_section_m_share.parquet"
LOG_DIR = DEV_AI_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- CIIU Rev.4 section-letter → 2-digit-range mapping -------------------
# Canonical per ISIC Rev.4 / DANE CIIU 4 a.c. publication; mirrors Pair D verbatim.
# Spec §5.1 v1.0.1 NIT-2 closure: Section J = Divisions {58,59,60,61,62,63};
# Section M = Divisions {69,70,71,72,73,74,75}.

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
    "J": set(range(58, 64)),     # 58-63 Information/communication  -- PRIMARY (Y_p)
    "K": set(range(64, 67)),     # 64-66 Finance/insurance
    "L": {68},                   # Real estate
    "M": set(range(69, 76)),     # 69-75 Professional/scientific/technical -- SENSITIVITY (Y_s2)
    "N": set(range(77, 83)),     # 77-82 Administrative/support
    "O": {84},                   # Public administration
    "P": {85},                   # Education
    "Q": set(range(86, 89)),     # 86-88 Human health/social
    "R": set(range(90, 94)),     # 90-93 Arts/entertainment
    "S": set(range(94, 97)),     # 94-96 Other services
    "T": set(range(97, 99)),     # 97-98 Households as employers
    "U": {99},                   # Extra-territorial
}

PRIMARY_SECTION = "J"
SENSITIVITY_SECTION = "M"


@dataclass(frozen=True)
class FilePlan:
    """One ingestion job. Mirrors Pair D FilePlan verbatim for catalog compatibility."""
    year: int
    month: int
    era: str  # "empalme_2015_2020" | "marco2018_sem_2021" | "marco2018_native"
    download_url: str
    cache_path: Path
    inner_path_match: str
    char_inner_match: str
    fex_col: str           # "FEX_C" or "FEX_C18"
    rama_col: str          # "RAMA4D_R4"
    file_id: int


SPANISH_MONTHS = {
    1: ("Enero", "ENE"), 2: ("Febrero", "FEB"), 3: ("Marzo", "MAR"),
    4: ("Abril", "ABR"), 5: ("Mayo", "MAY"), 6: ("Junio", "JUN"),
    7: ("Julio", "JUL"), 8: ("Agosto", "AGO"), 9: ("Septiembre", "SEP"),
    10: ("Octubre", "OCT"), 11: ("Noviembre", "NOV"), 12: ("Diciembre", "DIC"),
}


# Canonical column aliases (case-insensitive). Inherits Pair D's tolerance set verbatim;
# DANE publishes the same semantic column under varying capitalizations within the same
# Empalme catalog (e.g. 2020-01 has `RAMA4D_R4`, 2020-03 has `Rama4d_r4`).
_COL_ALIASES_UPPER: dict[str, str] = {
    "RAMA4D_R4": "RAMA4D_R4",
    "RAMA4D_R4 ": "RAMA4D_R4",   # trailing-space tolerance
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
    """Rename DataFrame columns to spec-canonical names (case-insensitive, trailing-whitespace tolerant)."""
    rename: dict[str, str] = {}
    for c in df.columns:
        key = c.strip().upper()
        if key in _COL_ALIASES_UPPER:
            rename[c] = _COL_ALIASES_UPPER[key]
    return df.rename(columns=rename)


def _detect_csv_format(blob: bytes) -> tuple[str, str]:
    """Return (encoding, separator). Inherits Pair D logic — full-blob UTF-8 then Latin-1 fallback."""
    try:
        blob.decode("utf-8")
        enc = "utf-8"
    except UnicodeDecodeError:
        enc = "latin-1"
    head = blob[:8000].decode(enc, errors="replace")
    line0 = head.split("\n", 1)[0]
    sep = ";" if line0.count(";") > line0.count(",") else ","
    return enc, sep


def _decode_csv_to_df(blob: bytes, want_cols: list[str]) -> pd.DataFrame:
    """Decode CSV bytes, canonicalize column names, return only want_cols subset."""
    enc, sep = _detect_csv_format(blob)
    df = pd.read_csv(
        io.BytesIO(blob), sep=sep, encoding=enc,
        low_memory=False, dtype=str,
        on_bad_lines="warn",
    )
    df = _canonicalize_columns(df)
    keep = [c for c in want_cols if c in df.columns]
    return df[keep]


def _basename_lower(zip_inner_path: str) -> str:
    return zip_inner_path.rsplit("/", 1)[-1].lower()


def _is_ocupados_csv(zip_inner_path: str) -> bool:
    return _basename_lower(zip_inner_path) in ("ocupados.csv",)


def _is_caracteristicas_csv(zip_inner_path: str) -> bool:
    bn = _basename_lower(zip_inner_path)
    if not bn.endswith(".csv"):
        return False
    return "aracter" in bn  # robust ascii prefix vs Latin-1 mojibake variants


def _http_get(url: str, dest: Path, timeout: int = 600) -> None:
    """Download URL to dest if not cached. Per §9.14, no paid-tier substitution permitted."""
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


def _classify_section(rama4d: str) -> str | None:
    """Map a 4-digit CIIU Rev.4 code to its section letter, or None."""
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


def _logit(p: float) -> float:
    if not (0 < p < 1):
        return float("nan")
    return math.log(p / (1 - p))


def _load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


# --- Plan building (mirrors Pair D verbatim) -----------------------------

def _build_plans(manifest: dict) -> list[FilePlan]:
    """Build full ingest plan for 2015-01 → 2026-03 (inclusive of 2026-Mar tolerance).

    Mirrors Pair D `_build_plans` verbatim; reuses Pair D's manifest and download cache.
    Per spec §4 + plan Task 1.1 Step 2: monthly window 2015-01 → 2026-03 with one-month
    publication-lag tolerance at end-of-window.
    """
    plans: list[FilePlan] = []

    # 2015-2020: Empalme catalogs (annual zip; per-month sub-zip + Ocupados.CSV)
    for yr in range(2015, 2021):
        ent = manifest[str(yr)]["empalme"]
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

    for mo in range(1, 7):
        sp_name, _ = SPANISH_MONTHS[mo]
        plans.append(FilePlan(
            year=2021, month=mo, era="marco2018_sem_2021",
            download_url=sem1["download_url"], cache_path=sem1_cache,
            inner_path_match=f"{sp_name} 2021/CSV",
            char_inner_match=f"{sp_name} 2021/CSV",
            fex_col="FEX_C18", rama_col="RAMA4D_R4",
            file_id=sem1["file_id"],
        ))

    for mo in range(7, 13):
        sp_name, _ = SPANISH_MONTHS[mo]
        plans.append(FilePlan(
            year=2021, month=mo, era="marco2018_sem_2021",
            download_url=sem2["download_url"], cache_path=sem2_cache,
            inner_path_match=f"{sp_name} 2021/CSV",
            char_inner_match=f"{sp_name} 2021/CSV",
            fex_col="FEX_C18", rama_col="RAMA4D_R4",
            file_id=sem2["file_id"],
        ))

    # 2022-2026: per-month files; tokenizer-based filename matching (DANE filename heterogeneity).
    def _tokenize_fn(fn: str) -> set[str]:
        return set(
            fn.lower()
              .replace("/", " ").replace("-", " ").replace("_", " ").replace(".", " ")
              .split()
        )

    def _match_monthly(year: int, mo: int, monthly: dict[str, dict]) -> dict | None:
        sp_full, _ = SPANISH_MONTHS[mo]
        sp_full_l = sp_full.lower()
        sp_pre3 = sp_full[:3].lower()
        for fn, f in monthly.items():
            tokens = _tokenize_fn(fn)
            if sp_full_l not in tokens and sp_pre3 not in tokens:
                continue
            for tok in tokens:
                if tok.isdigit() and len(tok) == 4 and tok != str(year):
                    if tok == "2018":  # Marco-2018 marker permitted
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

    # 2026: Pair D included only Jan + Feb (publication-lag rule). The plan target window
    # is 2015-01 → 2026-03 with one-month tolerance, so we MIRROR Pair D's actual realized
    # endpoint here. If 2026-03 file exists in manifest we include it; otherwise tolerance
    # absorbs the drop.
    monthly_2026 = {f["filename"]: f for f in manifest["2026"]["native"]["files"]}
    for mo in (1, 2, 3):
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

def _ingest_month(plan: FilePlan) -> dict:
    """Produce one monthly Y data row (Section J + Section M cells) from a FilePlan.

    Returns dict with keys:
      year, month, era, fex_total, fex_section_j, fex_section_m,
      n_young_employed, n_young_in_section_j, n_young_in_section_m,
      Y_section_j_raw, Y_section_m_raw

    Per spec §5.1: numerator = young-employed in target section; denominator = young-employed.
    Universe: national aggregate (Cabecera + Resto are NOT separated in GEIH micro-data —
    the underlying frame already includes both; the `AREA` column only distinguishes 13 ciudades vs.
    cabeceras vs. centros poblados / rural disperso, and per spec §4 we sum across all of them).
    """
    _http_get(plan.download_url, plan.cache_path)

    # Empalme 2015-2020: outer annual zip → 12 inner per-month zips → Ocupados + Características.
    if plan.era == "empalme_2015_2020":
        sp_name, _ = SPANISH_MONTHS[plan.month]
        with zipfile.ZipFile(plan.cache_path) as outer:
            inner_candidates = [
                n for n in outer.namelist()
                if n.lower().endswith(".zip")
                and f"{plan.month}. {sp_name.lower()}.zip" in n.lower()
            ]
            if not inner_candidates:
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
        sp_full, _ = SPANISH_MONTHS[plan.month]
        sp_prefix3 = sp_full[:3].lower()
        with zipfile.ZipFile(plan.cache_path) as z:
            names = z.namelist()

            def _path_matches_month(p: str) -> bool:
                pl = p.lower()
                tokens = (
                    pl.replace("/", " ").replace("-", " ").replace("_", " ").split()
                )
                return sp_full.lower() in tokens or sp_prefix3 in tokens

            oc_names = [n for n in names if _path_matches_month(n) and _is_ocupados_csv(n)]
            if not oc_names:
                raise FileNotFoundError(
                    f"2021-{plan.month:02d} Ocupados.CSV not found in semester archive "
                    f"({plan.cache_path.name}); month_token={sp_full}/{sp_prefix3}"
                )
            oc_name = oc_names[0]
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
                # Possibly nested zip
                inners = [n for n in names if n.lower().endswith(".zip")]
                got = False
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
                            got = True
                            break
                if not got:
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
    pk_cols = ["DIRECTORIO", "SECUENCIA_P", "ORDEN", "HOGAR"]
    oc_cols = pk_cols + [plan.fex_col, plan.rama_col]
    ch_cols = pk_cols + ["P6040"]

    df_oc = _decode_csv_to_df(oc_blob, oc_cols)
    df_ch = _decode_csv_to_df(ch_blob, ch_cols)

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

    df_ch["P6040"] = pd.to_numeric(df_ch["P6040"], errors="coerce")
    df_oc[plan.fex_col] = pd.to_numeric(df_oc[plan.fex_col], errors="coerce")

    # Inner join on PK (m:1 — Pair D precedent for cross-listed-household tolerance).
    merged = df_oc.merge(df_ch, on=pk_cols, how="inner", validate="m:1")

    # Filter youth band 14-28 inclusive (Ley 1622 de 2013).
    youth = merged[(merged["P6040"] >= 14) & (merged["P6040"] <= 28)].copy()
    youth = youth[youth[plan.fex_col] > 0]

    # Section letter via 4-digit Rev.4 code.
    youth["_section"] = youth[plan.rama_col].apply(_classify_section)

    fex = plan.fex_col
    fex_total = float(youth[fex].sum())
    fex_section_j = float(youth[youth["_section"] == "J"][fex].sum())
    fex_section_m = float(youth[youth["_section"] == "M"][fex].sum())

    n_total = int(len(youth))
    n_section_j = int((youth["_section"] == "J").sum())
    n_section_m = int((youth["_section"] == "M").sum())

    Y_j_raw = fex_section_j / fex_total if fex_total > 0 else float("nan")
    Y_m_raw = fex_section_m / fex_total if fex_total > 0 else float("nan")

    return {
        "year": plan.year,
        "month": plan.month,
        "era": plan.era,
        "fex_total": fex_total,
        "fex_section_j": fex_section_j,
        "fex_section_m": fex_section_m,
        "n_young_employed": n_total,
        "n_young_in_section_j": n_section_j,
        "n_young_in_section_m": n_section_m,
        "Y_section_j_raw": Y_j_raw,
        "Y_section_m_raw": Y_m_raw,
    }


# --- Main -----------------------------------------------------------------

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
                f"era={plan.era:>20s} n_total={row['n_young_employed']:>5d} "
                f"n_J={row['n_young_in_section_j']:>4d} Y_J={row['Y_section_j_raw']:.4f} "
                f"n_M={row['n_young_in_section_m']:>4d} Y_M={row['Y_section_m_raw']:.4f} "
                f"({elapsed:.1f}s)"
            )
        except Exception as e:  # noqa: BLE001
            print(f"[{i+1:3d}/{len(plans)}] {plan.year}-{plan.month:02d} FAILED: {e}")
            failures.append((plan, str(e)))

    if not rows:
        print("No rows produced. Aborting.")
        return 1

    df = pd.DataFrame(rows)
    # Use last-calendar-day-of-month UTC to match cop_usd_panel.parquet convention (Task 1.2).
    df["year_month"] = (
        pd.to_datetime({"year": df["year"], "month": df["month"], "day": 1}, utc=True)
        + pd.offsets.MonthEnd(0)
    )
    df = df.sort_values("year_month").reset_index(drop=True)

    # ----- Section J (Y_p, primary) -----
    df_j = pd.DataFrame({
        "year_month": df["year_month"],
        "raw_share": df["Y_section_j_raw"],
        "logit_share": df["Y_section_j_raw"].apply(_logit),
        "cell_count": df["n_young_in_section_j"].astype("int64"),
        "FEX_total": df["fex_total"],
        # diagnostic columns:
        "fex_section_j": df["fex_section_j"],
        "n_young_employed": df["n_young_employed"].astype("int64"),
        "era": df["era"].astype("string"),
    })
    df_j.to_parquet(OUT_J, index=False)
    print(f"Wrote {OUT_J} ({len(df_j)} rows)")

    # ----- Section M (Y_s2, sensitivity / R2) -----
    df_m = pd.DataFrame({
        "year_month": df["year_month"],
        "raw_share": df["Y_section_m_raw"],
        "logit_share": df["Y_section_m_raw"].apply(_logit),
        "cell_count": df["n_young_in_section_m"].astype("int64"),
        "FEX_total": df["fex_total"],
        "fex_section_m": df["fex_section_m"],
        "n_young_employed": df["n_young_employed"].astype("int64"),
        "era": df["era"].astype("string"),
    })
    df_m.to_parquet(OUT_M, index=False)
    print(f"Wrote {OUT_M} ({len(df_m)} rows)")

    # ----- Per-month diagnostic table emitted to logs -----
    diag = df[[
        "year_month", "era",
        "n_young_employed", "n_young_in_section_j", "n_young_in_section_m",
        "Y_section_j_raw", "Y_section_m_raw",
    ]].copy()
    diag_path = LOG_DIR / "per_month_cell_counts.csv"
    diag.to_csv(diag_path, index=False)
    print(f"Wrote {diag_path}")

    # ----- Anomaly flags (diagnostic per plan Task 1.1 Step 5) -----
    # Y feasibility memo §1.1 baseline for Section J cell: 700-1,200 per month.
    # Pair D broad services baseline: 7,000-9,000 per month.
    # We surface (NOT auto-trigger HALT) any month whose Section-J cell visibly deviates
    # from the [700, 1200] band. Section M is documented but no pre-pinned numeric threshold.
    j_low_band, j_high_band = 700, 1200
    j_anomalies = diag[(diag["n_young_in_section_j"] < j_low_band) |
                       (diag["n_young_in_section_j"] > j_high_band)].copy()
    if len(j_anomalies) > 0:
        print(f"\n[DIAGNOSTIC] {len(j_anomalies)} months with Section J cell-count outside Y feasibility memo §1.1 baseline [{j_low_band}, {j_high_band}]:")
        print(j_anomalies[["year_month", "n_young_employed", "n_young_in_section_j", "Y_section_j_raw"]].to_string(index=False))

    if failures:
        print(f"\n{len(failures)} failures:")
        for p, err in failures:
            print(f"  {p.year}-{p.month:02d} {p.era}: {err[:200]}")

    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
