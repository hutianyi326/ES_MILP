"""Compare UO technology labels from archived OMIE unit-list snapshots.

The archived PDF is an Internet Archive capture of an OMIE-published file.  It is
kept as auxiliary historical evidence and is never treated as an immutable OMIE
version unless the original OMIE publication is independently confirmed.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[3]
ARCHIVED_PDF = ROOT / "data/raw/ES/omie/unit_list/20250911T035831Z_wayback/LISTA_UNIDADES.PDF"
UOF_PATH = ROOT / "data/processed/ES/omie_uof_sell_matched_20250101_20250318_evening.csv"
CURRENT_PATH = ROOT / "data/processed/ES/omie_uof_technology_crosswalk_candidate_20260904.csv"
OUTPUT_PATH = ROOT / "data/processed/ES/omie_uof_technology_crosswalk_archived_20250910.csv"
COMPARE_PATH = ROOT / "data/processed/ES/omie_uof_technology_crosswalk_compare_20250910_20260904.csv"


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower()


def map_technology(raw: str) -> str:
    value = _norm(raw)
    if "ciclo combinado" in value:
        return "CCGT"
    if "bombeo" in value:
        return "PumpedHydro"
    if "hidraulica" in value:
        return "Hydro"
    if "eolica" in value:
        return "Wind"
    if "solar fotovolta" in value:
        return "SolarPV"
    if "solar term" in value:
        return "SolarThermal"
    if "nuclear" in value:
        return "Nuclear"
    if "carbon" in value:
        return "Coal"
    if any(token in value for token in ("termica renovable", "cogener", "residuo", "biomasa")):
        return "RenewCogRes"
    if "almacenamiento" in value:
        return "Storage"
    return ""


def parse_unit_list(pdf_path: Path = ARCHIVED_PDF) -> dict[str, dict[str, str]]:
    """Extract unit rows from the tabular PDF, keyed by UO code."""
    units: dict[str, dict[str, str]] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables() or []:
                if not table or not table[0] or "CODIGO" not in (table[0][0] or ""):
                    continue
                for raw_row in table[1:]:
                    if not raw_row or not raw_row[0]:
                        continue
                    row = [(cell or "").replace("\n", " ").strip() for cell in raw_row]
                    if len(row) < 7 or not re.match(r"^[A-Z0-9]+$", row[0]):
                        continue
                    units[row[0]] = {
                        "unit_of_offer": row[0],
                        "unit_description": row[1],
                        "agent_owner": row[2],
                        "unit_type": row[4],
                        "zone": row[5],
                        "raw_technology": row[6],
                        "mapped_technology": map_technology(row[6]),
                        "source_page": str(page_number),
                    }
    return units


def _load_sample_units(path: Path = UOF_PATH) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["unit_of_offer"] for row in csv.DictReader(handle)}


def _load_current(path: Path = CURRENT_PATH) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["unit_of_offer"]: row for row in csv.DictReader(handle)}


def build_comparison(
    archived_pdf: Path = ARCHIVED_PDF,
    uof_path: Path = UOF_PATH,
    current_path: Path = CURRENT_PATH,
    output_path: Path = OUTPUT_PATH,
    compare_path: Path = COMPARE_PATH,
) -> dict[str, int]:
    archived = parse_unit_list(archived_pdf)
    sample_units = _load_sample_units(uof_path)
    current = _load_current(current_path)

    out_fields = [
        "unit_of_offer", "archived_unit_type", "archived_zone", "archived_raw_technology",
        "archived_mapped_technology", "archived_source_page", "archived_source_issued_at",
        "archived_source_kind", "current_mapped_technology", "current_raw_technology",
        "mapping_comparison", "historical_applicability",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=out_fields)
        writer.writeheader()
        for unit in sorted(sample_units):
            old = archived.get(unit, {})
            now = current.get(unit, {})
            old_map = old.get("mapped_technology", "")
            now_map = now.get("mapped_technology", "")
            if not old:
                comparison = "not_in_archived_20250910_list"
            elif old_map and now_map and old_map == now_map:
                comparison = "same_category_in_archived_and_current"
            elif old_map and now_map and old_map != now_map:
                comparison = "category_differs"
            elif old_map or now_map:
                comparison = "mapped_in_one_snapshot_only"
            else:
                comparison = "unmapped_in_both_snapshots"
            writer.writerow(
                {
                    "unit_of_offer": unit,
                    "archived_unit_type": old.get("unit_type", ""),
                    "archived_zone": old.get("zone", ""),
                    "archived_raw_technology": old.get("raw_technology", ""),
                    "archived_mapped_technology": old_map,
                    "archived_source_page": old.get("source_page", ""),
                    "archived_source_issued_at": "2025-09-10 15:02",
                    "archived_source_kind": "internet_archive_capture_of_OMIE_PDF",
                    "current_mapped_technology": now_map,
                    "current_raw_technology": now.get("raw_technology", ""),
                    "mapping_comparison": comparison,
                    "historical_applicability": "auxiliary_snapshot_not_final_ground_truth",
                }
            )

    compare_fields = ["mapping_comparison"]
    counts: dict[str, int] = {}
    with output_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = row["mapping_comparison"]
            counts[key] = counts.get(key, 0) + 1
    with compare_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "count"])
        writer.writeheader()
        for key in sorted(counts):
            writer.writerow({"metric": key, "count": counts[key]})
    return {"sample_uos": len(sample_units), "archived_units": len(archived), **counts}


if __name__ == "__main__":
    print(build_comparison())
