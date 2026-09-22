"""Backfill the stable Step 7 provenance columns in generated proxy CSVs.

This is intentionally a small, idempotent repair for outputs generated before
the metadata columns were added to ``extend_near_marginal_proxy``.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "data/processed/ES"
FILES = (
    PROCESSED / "omie_near_marginal_proxy_20250319_20250930_evening_hourly.csv",
    PROCESSED / "omie_near_marginal_proxy_20251001_20260731_evening_15min.csv",
)


def repair(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return 0
    is_qh = any(row.get("period_granularity") == "15min" for row in rows)
    fields = list(rows[0])
    required = ["data_date", "timezone", "market_version", "issued_at", "retrieved_at", "source_file"]
    for field in required:
        if field not in fields:
            fields.insert(fields.index("delivery_date") + 1 if field == "data_date" else len(fields), field)
    for row in rows:
        row.setdefault("data_date", row.get("delivery_date", ""))
        row.setdefault("timezone", "Europe/Madrid")
        row.setdefault("market_version", "DA_15MIN_MTU" if is_qh else "DA_HOURLY")
        row.setdefault("issued_at", "")
        row["retrieved_at"] = row.get("retrieved_at", "") or row.get("price_retrieved_at", "") or row.get("uof_retrieved_at", "")
        row.setdefault("source_file", row.get("uof_source_file", ""))
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)
    return len(rows)


if __name__ == "__main__":
    for target in FILES:
        print(target.name, repair(target))
