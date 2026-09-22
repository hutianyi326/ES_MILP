"""Run a reproducible quality audit for the Step 7 proxy outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import zipfile
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .extend_near_marginal_proxy import END, _expected_periods


ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "data/processed/ES"
RAW = ROOT / "data/raw/ES"
OUTPUTS = (
    PROCESSED / "omie_near_marginal_proxy_20250319_20250930_evening_hourly.csv",
    PROCESSED / "omie_near_marginal_proxy_20251001_20260731_evening_15min.csv",
)
REQUIRED = ("data_date", "timezone", "market_version", "retrieved_at", "source_file", "price_regime", "crosswalk_version")
TECHNOLOGIES = ("CCGT", "Hydro", "PumpedHydro", "Wind", "SolarPV", "RenewCogRes", "Nuclear", "Coal", "Other")


def _float(row: dict[str, str], field: str) -> float:
    value = row.get(field, "")
    return float(value) if value not in (None, "") else 0.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _audit_output(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    keys = {(row.get("delivery_date", ""), row.get("period", "")) for row in rows}
    local = [datetime.fromisoformat(row["local_datetime"]) for row in rows]
    required_missing = {field: sum(not row.get(field) for row in rows) for field in REQUIRED}
    arithmetic_failures = 0
    share_max_error = 0.0
    max_crosswalk_error = 0.0
    negative_mw_rows = 0
    for row in rows:
        total = _float(row, "nm_total_mw")
        mapped = _float(row, "nm_mapped_mw")
        unmapped = _float(row, "nm_unmapped_mw")
        tech_total = sum(_float(row, f"{tech}_NM_MW") for tech in TECHNOLOGIES)
        share_total = sum(_float(row, f"{tech}_NMShare_all") for tech in TECHNOLOGIES)
        if total > 0:
            share_max_error = max(share_max_error, abs(share_total - 1.0))
        max_crosswalk_error = max(max_crosswalk_error, abs(mapped + unmapped - total))
        if abs(tech_total - total) > 1e-5 or abs(mapped + unmapped - total) > 1e-5 or (total > 0 and abs(share_total - 1.0) > 1e-6):
            arithmetic_failures += 1
        if any(_float(row, f"{tech}_NM_MW") < -1e-9 for tech in TECHNOLOGIES) or total < -1e-9:
            negative_mw_rows += 1
    source_paths = {Path(row.get("price_source_path", "")) for row in rows if row.get("price_source_path")}
    uof_paths = {Path(row.get("uof_source_zip_path", "")) for row in rows if row.get("uof_source_zip_path")}
    return {
        "file": str(path),
        "rows": len(rows),
        "unique_keys": len(keys),
        "duplicate_keys": len(rows) - len(keys),
        "date_min": min((row.get("delivery_date", "") for row in rows), default=""),
        "date_max": max((row.get("delivery_date", "") for row in rows), default=""),
        "local_hours": sorted({item.hour for item in local}),
        "bad_evening_hours": sum(item.hour not in {19, 20, 21, 22} for item in local),
        "timezone_values": sorted({row.get("timezone", "") for row in rows}),
        "market_versions": dict(Counter(row.get("market_version", "") for row in rows)),
        "granularities": dict(Counter(row.get("period_granularity", "") for row in rows)),
        "official_setter_nonblank": sum(bool(row.get("official_setter_labels")) for row in rows),
        "required_metadata_missing": required_missing,
        "arithmetic_failures": arithmetic_failures,
        "share_max_error": share_max_error,
        "crosswalk_conservation_max_error_mw": max_crosswalk_error,
        "negative_nm_mw_rows": negative_mw_rows,
        "source_price_paths_missing": sum(not path.exists() for path in source_paths),
        "source_uof_zip_paths_missing": sum(not path.exists() for path in uof_paths),
        "price_missing_rows": sum(not row.get("price_eur_mwh") for row in rows),
        "nonfinite_price_rows": sum(not math.isfinite(_float(row, "price_eur_mwh")) for row in rows),
        "revised_price_files": dict(Counter(row.get("price_source_file", "") for row in rows if re.search(r"\.\d+$", row.get("price_source_file", "")) and not row.get("price_source_file", "").endswith(".1"))),
    }


def _audit_coverage() -> dict[str, Any]:
    result: dict[str, Any] = {}
    windows = [
        ("hourly", date(2025, 3, 19), date(2025, 9, 30), OUTPUTS[0]),
        ("qh", date(2025, 10, 1), END, OUTPUTS[1]),
    ]
    for name, start, end, path in windows:
        with path.open("r", encoding="utf-8", newline="") as handle:
            observed = {(row["delivery_date"], int(row["period"])) for row in csv.DictReader(handle)}
        expected = _expected_periods(start, end)
        missing = expected - observed
        result[name] = {"expected": len(expected), "observed": len(observed), "missing": len(missing), "missing_by_month": dict(sorted(Counter(delivery[:7] for delivery, _period in missing).items())), "missing_dates": sorted({delivery for delivery, _period in missing})}
    return result


def _audit_repair_files() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for path in RAW.glob("omie/*/*/marginalpdbc_20251030.3"):
        records.append({"path": str(path), "exists": path.exists(), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    for path in RAW.glob("omie/*/*/marginalpdbc_20251127.2"):
        records.append({"path": str(path), "exists": path.exists(), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    packages: dict[str, Any] = {}
    for month in ("2025-10", "2025-11", "2026-06", "2026-07"):
        candidates = list((RAW / "omie" / month).glob("**/curva_pbc_uof_*.zip"))
        if not candidates:
            packages[month] = {"available": False, "daily_members": 0}
            continue
        package = max(candidates, key=lambda item: item.stat().st_mtime)
        try:
            with zipfile.ZipFile(package) as archive:
                daily = len([name for name in archive.namelist() if name.endswith(".1")])
            packages[month] = {"available": True, "daily_members": daily, "path": str(package), "bytes": package.stat().st_size}
        except zipfile.BadZipFile:
            packages[month] = {"available": False, "daily_members": 0, "bad_zip": True, "path": str(package)}
    return {"revised_price_files": records, "uof_package_members": packages}


def run() -> dict[str, Any]:
    return {"outputs": [_audit_output(path) for path in OUTPUTS], "coverage": _audit_coverage(), "repair": _audit_repair_files()}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
