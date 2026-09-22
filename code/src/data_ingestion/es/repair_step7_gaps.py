"""Try official OMIE revision files for the remaining Step 7 gaps.

The routine never overwrites an existing raw file.  It records every
candidate URL and response in a new immutable retrieval batch.  Missing UOF
months are intentionally not synthesized: the 2026-06 and 2026-07 package
gaps require a complete official monthly archive, not a price-file revision.
"""

from __future__ import annotations

import json
import csv
import urllib.error
import urllib.parse
from datetime import date
from pathlib import Path
from typing import Any

from .common import is_html, iso_now, json_dump, retrieval_batch_id, safe_write_bytes, sha256_bytes
from .extend_near_marginal_proxy import (
    END,
    QH_PATH,
    QH_QUALITY_PATH,
    _expected_periods,
    _get,
    _latest_raw_file,
    _load_crosswalk,
    _parse_member_rows,
    _price_index,
    _price_manifest_index,
    _uof_retrieved_at,
    _write_csv,
)
from .omie import normalize_omie_directory


ROOT = Path(__file__).resolve().parents[3]
RAW_ROOT = ROOT / "data/raw/ES"

# OMIE occasionally keeps a corrected DA price under a numeric revision
# suffix.  The first entry is the revision observed in the official archive.
PRICE_CANDIDATES: dict[str, list[str]] = {
    "2025-10-30": ["marginalpdbc_20251030.3", "marginalpdbc_20251030.2", "marginalpdbc_20251030.1"],
    "2025-11-27": ["marginalpdbc_20251127.3", "marginalpdbc_20251127.2", "marginalpdbc_20251127.1"],
}


def _url(filename: str) -> str:
    query = urllib.parse.urlencode({"filename": filename, "parents": "marginalpdbc"})
    return f"https://www.omie.es/en/file-download?{query}"


def _existing(month: str, filename: str) -> Path | None:
    paths = list((RAW_ROOT / "omie" / month).glob(f"**/{filename}"))
    return max(paths, key=lambda item: item.stat().st_mtime) if paths else None


def run() -> dict[str, Any]:
    batch = retrieval_batch_id()
    all_records: list[dict[str, Any]] = []
    repaired: list[dict[str, Any]] = []
    for delivery_date, candidates in PRICE_CANDIDATES.items():
        month = delivery_date[:7]
        for filename in candidates:
            existing = _existing(month, filename)
            if existing is not None:
                record = {"delivery_date": delivery_date, "filename": filename, "url": _url(filename), "status": "existing", "http_status": 200, "path": str(existing), "bytes": existing.stat().st_size, "sha256": sha256_bytes(existing.read_bytes())}
                all_records.append(record)
                repaired.append(record)
                break
            url = _url(filename)
            try:
                status, headers, body = _get(url, timeout=90.0)
                error = ""
            except urllib.error.URLError as exc:
                status, headers, body = 0, {}, b""
                error = str(exc.reason if hasattr(exc, "reason") else exc)
            target = RAW_ROOT / "omie" / month / batch / filename
            record: dict[str, Any] = {"source": "omie", "dataset": "OMIE_DA_PRICE_ES", "kind": "da", "period": month, "delivery_date": delivery_date, "url": url, "retrieved_at": iso_now(), "http_status": status, "bytes": len(body), "sha256": sha256_bytes(body), "filename": filename, "path": str(target), "status": "failed"}
            if error:
                record["error"] = error
            if status == 200 and body and not is_html(body):
                target.parent.mkdir(parents=True, exist_ok=True)
                record["status"] = "success" if safe_write_bytes(target, body) else "already_exists"
                repaired.append(record)
                all_records.append(record)
                break
            if status == 200 and is_html(body):
                record["status"] = "failed_html_response"
            all_records.append(record)
    manifest_dir = RAW_ROOT / "omie" / "gap_repair" / batch
    json_dump(manifest_dir / "manifest.json", {"schema": "ES-DATA-07/gap-repair-v1", "source": "omie", "retrieval_batch": batch, "records": all_records})
    patched = _patch_qh_rows()
    return {"batch": batch, "repaired": repaired, "attempts": all_records, "patched_qh": patched}


def _patch_qh_rows() -> dict[str, Any]:
    """Parse only recovered delivery days and merge them into the QH output."""
    target_dates = {date(2025, 10, 30), date(2025, 11, 27)}
    normalized = normalize_omie_directory(RAW_ROOT, min(target_dates), max(target_dates), kinds=["da"])
    prices = _price_index(normalized, _price_manifest_index())
    crosswalk = _load_crosswalk()
    replacements: list[dict[str, Any]] = []
    for delivery in sorted(target_dates):
        month = delivery.strftime("%Y-%m")
        package = _latest_raw_file(f"omie/{month}/**/curva_pbc_uof_{delivery:%Y%m}.zip")
        if package is None:
            continue
        member_name = f"curva_pbc_uof_{delivery:%Y%m%d}.1"
        import zipfile
        with zipfile.ZipFile(package) as archive:
            if member_name not in archive.namelist():
                continue
            rows = _parse_member_rows(archive, member_name, prices, crosswalk)
        for row in rows:
            row["uof_source_zip"] = package.name
            row["uof_source_zip_path"] = str(package)
            row["uof_retrieved_at"] = _uof_retrieved_at(package)
        replacements.extend(rows)
    if not replacements or not QH_PATH.exists():
        return {"replaced_dates": [], "rows_added": 0}
    with QH_PATH.open("r", encoding="utf-8", newline="") as handle:
        existing = list(csv.DictReader(handle))
    target_text = {delivery.isoformat() for delivery in target_dates}
    kept = [row for row in existing if row.get("delivery_date") not in target_text]
    combined = kept + replacements
    combined.sort(key=lambda row: (str(row.get("delivery_date", "")), int(row.get("period", 0))))
    _write_csv(QH_PATH, combined)
    _refresh_qh_quality(combined)
    return {"replaced_dates": sorted({row["delivery_date"] for row in replacements}), "rows_added": len(replacements)}


def _refresh_qh_quality(rows: list[dict[str, Any]]) -> None:
    expected = _expected_periods(date(2025, 10, 1), END)
    observed = {(str(row["delivery_date"]), int(row["period"])) for row in rows}
    full_prices = _price_index(
        normalize_omie_directory(RAW_ROOT, date(2025, 10, 1), END, kinds=["da"]),
        _price_manifest_index(),
    )
    price_keys = set(full_prices)
    missing = expected - observed
    missing_by_month: dict[str, int] = {}
    for delivery, _period in missing:
        missing_by_month[delivery[:7]] = missing_by_month.get(delivery[:7], 0) + 1
    quality = json.loads(QH_QUALITY_PATH.read_text(encoding="utf-8"))
    quality.update(
        {
            "status": "conditional_proxy_extension" if not missing else "conditional_proxy_extension_partial",
            "rows": len(rows),
            "unique_delivery_period_keys": len(observed),
            "missing_expected_keys": len(missing),
            "missing_expected_keys_by_month": dict(sorted(missing_by_month.items())),
            "missing_expected_dates": sorted({delivery for delivery, _period in missing}),
            "price_keys_observed": len(price_keys),
            "price_missing_expected_keys": len(expected - price_keys),
            "rows_with_nm_selected": sum(float(row.get("nm_total_mw") or 0) > 0 for row in rows),
            "nonpositive_price_rows": sum(row.get("price_regime") in {"zero", "negative"} for row in rows),
            "market_rows_used": {market: sum(row.get("market_rows_used") == market for row in rows) for market in ("MI", "ES")},
        }
    )
    json_dump(QH_QUALITY_PATH, quality)


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
