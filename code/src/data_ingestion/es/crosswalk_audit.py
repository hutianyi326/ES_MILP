"""Build a historical-activity audit for the OMIE UO technology candidate map.

The public OMIE unit list is a current snapshot, so this module deliberately does
not promote its technology labels to historical truth.  It only joins the current
candidate labels to UOs observed in the 2025-01-01--2025-03-18 evening UOF sample
and records the historical activity evidence needed for a later manual review.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
UOF_PATH = ROOT / "data/processed/ES/omie_uof_sell_matched_20250101_20250318_evening.csv"
CANDIDATE_PATH = ROOT / "data/processed/ES/omie_uof_technology_crosswalk_candidate_20260904.csv"
OUTPUT_PATH = ROOT / "data/processed/ES/omie_uof_technology_crosswalk_historical_audit_20260905.csv"


def _join(values: set[str]) -> str:
    return ",".join(sorted(value for value in values if value))


def build_audit(
    uof_path: Path = UOF_PATH,
    candidate_path: Path = CANDIDATE_PATH,
    output_path: Path = OUTPUT_PATH,
) -> dict[str, int]:
    """Create the audit CSV and return row/coverage counts."""

    observed: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "dates": set(),
            "months": set(),
            "rows": 0,
            "energy_mwh": 0.0,
            "countries": set(),
            "market_scopes": set(),
        }
    )
    with uof_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            unit = row["unit_of_offer"]
            item = observed[unit]
            item["dates"].add(row["delivery_date"])
            item["months"].add(row["delivery_date"][:7])
            item["rows"] += 1
            item["energy_mwh"] += float(row["energy_mwh"] or 0)
            item["countries"].add(row["country_code"])
            item["market_scopes"].add(row["market_scope"])

    candidates: dict[str, dict[str, str]] = {}
    with candidate_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            candidates[row["unit_of_offer"]] = row

    fieldnames = [
        "unit_of_offer",
        "observed_2025_first_date",
        "observed_2025_last_date",
        "observed_2025_date_count",
        "observed_2025_months",
        "observed_all_three_months",
        "observed_uof_evening_rows",
        "observed_energy_mwh",
        "observed_country_codes",
        "observed_market_scopes",
        "unit_type",
        "zone",
        "raw_technology",
        "mapped_technology",
        "current_mapping_status",
        "historical_presence_evidence",
        "historical_technology_applicability",
        "crosswalk_version",
        "source_pdf",
        "source_issued_at",
        "source_page",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for unit in sorted(observed):
            activity = observed[unit]
            candidate = candidates.get(unit, {})
            dates = sorted(activity["dates"])
            months = sorted(activity["months"])
            mapped = candidate.get("mapped_technology", "")
            current_status = candidate.get("mapping_status", "unmapped_not_current_list")
            writer.writerow(
                {
                    "unit_of_offer": unit,
                    "observed_2025_first_date": dates[0],
                    "observed_2025_last_date": dates[-1],
                    "observed_2025_date_count": len(dates),
                    "observed_2025_months": ",".join(months),
                    "observed_all_three_months": int(len(months) == 3),
                    "observed_uof_evening_rows": activity["rows"],
                    "observed_energy_mwh": f'{activity["energy_mwh"]:.6f}',
                    "observed_country_codes": _join(activity["countries"]),
                    "observed_market_scopes": _join(activity["market_scopes"]),
                    "unit_type": candidate.get("unit_type", ""),
                    "zone": candidate.get("zone", ""),
                    "raw_technology": candidate.get("raw_technology", ""),
                    "mapped_technology": mapped,
                    "current_mapping_status": current_status,
                    "historical_presence_evidence": "observed_in_2025_evening_uof_sample",
                    "historical_technology_applicability": (
                        "unconfirmed_current_list_only" if mapped else "unconfirmed"
                    ),
                    "crosswalk_version": "candidate_20260904_plus_activity_audit_20260905",
                    "source_pdf": candidate.get("source_pdf", ""),
                    "source_issued_at": candidate.get("source_issued_at", ""),
                    "source_page": candidate.get("source_page", ""),
                }
            )

    return {
        "observed_uos": len(observed),
        "candidate_matches": sum(1 for unit in observed if unit in candidates),
        "rows": len(observed),
        "all_three_months": sum(1 for item in observed.values() if len(item["months"]) == 3),
    }


if __name__ == "__main__":
    print(build_audit())
